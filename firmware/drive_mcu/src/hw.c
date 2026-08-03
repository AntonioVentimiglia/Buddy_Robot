/* Hardware layer implementation — STM32G474RE via STM32Cube HAL.
 *
 * Compiles under PlatformIO (framework = stm32cube). Peripheral choices are
 * documented in docs/pin_map.md and docs/system_model/electrical_interfaces.md.
 * Bench-refinement TODOs are marked; the structure (which peripheral does what)
 * is final per the interface verification.
 */
#include "hw.h"

#include "buddy_config.h"
#include "pins.h"
#include "stm32g4xx_hal.h"

static TIM_HandleTypeDef htim1;                     /* PWM 20 kHz, 4 ch */
static TIM_HandleTypeDef henc[4];                   /* TIM2/3/4/8 encoder mode */
static ADC_HandleTypeDef hadc1;                     /* 4x CS channels */
static ADC_HandleTypeDef hadc2;                     /* vbat divider */
static UART_HandleTypeDef huart2;                   /* ST-LINK VCP */

/* RX ring buffer fed from the UART interrupt. */
#define RX_RING 512
static volatile uint8_t rx_ring[RX_RING];
static volatile uint16_t rx_head, rx_tail;
static uint8_t rx_byte;
static volatile uint32_t rx_error_count; /* UART errors seen; not yet in telemetry (39-byte payload is spec-locked) */

/* Encoder extension to 32-bit for the 16-bit timers (TIM3/4/8). */
static volatile int32_t enc_accum[4];
static uint16_t enc_last[4];

/* ---------------------------------------------------------------- clocks */
static void clock_init(void) {
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    /* HSI16 -> PLL -> 170 MHz SYSCLK */
    osc.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    osc.HSIState = RCC_HSI_ON;
    osc.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSI;
    osc.PLL.PLLM = RCC_PLLM_DIV4;  /* 16/4 = 4 MHz */
    osc.PLL.PLLN = 85;             /* 4*85 = 340 MHz VCO */
    osc.PLL.PLLR = RCC_PLLR_DIV2;  /* 170 MHz */
    osc.PLL.PLLP = RCC_PLLP_DIV2;
    osc.PLL.PLLQ = RCC_PLLQ_DIV2;
    HAL_RCC_OscConfig(&osc);

    HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1_BOOST);
    clk.ClockType = RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK |
                    RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV1;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_8);
}

/* ------------------------------------------------------------------ gpio */
static void gpio_out(GPIO_TypeDef *port, uint16_t pin) {
    GPIO_InitTypeDef g = {0};
    g.Pin = pin;
    g.Mode = GPIO_MODE_OUTPUT_PP;
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(port, &g);
}

static void gpio_in(GPIO_TypeDef *port, uint16_t pin, uint32_t pull) {
    GPIO_InitTypeDef g = {0};
    g.Pin = pin;
    g.Mode = GPIO_MODE_INPUT;
    g.Pull = pull;
    HAL_GPIO_Init(port, &g);
}

static void gpio_init_all(void) {
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_GPIOD_CLK_ENABLE();

    /* direction pins INA/INB x4 */
    for (int i = 0; i < 4; i++) {
        gpio_out(BUDDY_INA_PORT[i], BUDDY_INA_PIN[i]);
        gpio_out(BUDDY_INB_PORT[i], BUDDY_INB_PIN[i]);
        gpio_in(BUDDY_FAULT_PORT[i], BUDDY_FAULT_PIN[i], GPIO_PULLUP);
    }
    gpio_in(BUDDY_ESTOP_PORT, BUDDY_ESTOP_PIN, GPIO_PULLDOWN);
    gpio_out(BUDDY_LED_PORT, BUDDY_LED_PIN);
}

/* ------------------------------------------------------------------- pwm */
static void pwm_init(void) {
    __HAL_RCC_TIM1_CLK_ENABLE();
    GPIO_InitTypeDef g = {0};
    g.Pin = GPIO_PIN_8 | GPIO_PIN_9 | GPIO_PIN_10 | GPIO_PIN_11; /* PA8..PA11 */
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    g.Alternate = GPIO_AF6_TIM1;
    HAL_GPIO_Init(GPIOA, &g);

    htim1.Instance = TIM1;
    htim1.Init.Prescaler = 0;
    htim1.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim1.Init.Period = (170000000UL / BUDDY_PWM_HZ) - 1; /* 8499 @ 20 kHz */
    htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim1.Init.RepetitionCounter = 0;
    htim1.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    HAL_TIM_PWM_Init(&htim1);

    TIM_OC_InitTypeDef oc = {0};
    oc.OCMode = TIM_OCMODE_PWM1;
    oc.Pulse = 0;
    oc.OCPolarity = TIM_OCPOLARITY_HIGH;
    oc.OCFastMode = TIM_OCFAST_DISABLE;
    const uint32_t ch[4] = {TIM_CHANNEL_1, TIM_CHANNEL_2, TIM_CHANNEL_3,
                            TIM_CHANNEL_4};
    for (int i = 0; i < 4; i++) {
        HAL_TIM_PWM_ConfigChannel(&htim1, &oc, ch[i]);
        HAL_TIM_PWM_Start(&htim1, ch[i]);
    }
}

/* -------------------------------------------------------------- encoders */
static void encoder_one(TIM_HandleTypeDef *h, TIM_TypeDef *inst) {
    h->Instance = inst;
    h->Init.Prescaler = 0;
    h->Init.CounterMode = TIM_COUNTERMODE_UP;
    h->Init.Period = (inst == TIM2) ? 0xFFFFFFFFUL : 0xFFFF;
    h->Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    h->Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;

    TIM_Encoder_InitTypeDef e = {0};
    e.EncoderMode = TIM_ENCODERMODE_TI12; /* 4x counting */
    e.IC1Polarity = TIM_ICPOLARITY_RISING;
    e.IC1Selection = TIM_ICSELECTION_DIRECTTI;
    e.IC1Prescaler = TIM_ICPSC_DIV1;
    e.IC1Filter = 6; /* input filter vs brush noise (pin_map.md) */
    e.IC2Polarity = TIM_ICPOLARITY_RISING;
    e.IC2Selection = TIM_ICSELECTION_DIRECTTI;
    e.IC2Prescaler = TIM_ICPSC_DIV1;
    e.IC2Filter = 6;
    HAL_TIM_Encoder_Init(h, &e);
    HAL_TIM_Encoder_Start(h, TIM_CHANNEL_ALL);
}

static void encoders_init(void) {
    __HAL_RCC_TIM2_CLK_ENABLE();
    __HAL_RCC_TIM3_CLK_ENABLE();
    __HAL_RCC_TIM4_CLK_ENABLE();
    __HAL_RCC_TIM8_CLK_ENABLE();

    GPIO_InitTypeDef g = {0};
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = GPIO_PULLUP;
    g.Speed = GPIO_SPEED_FREQ_HIGH;

    g.Pin = GPIO_PIN_0 | GPIO_PIN_1; /* PA0/PA1 TIM2 */
    g.Alternate = GPIO_AF1_TIM2;
    HAL_GPIO_Init(GPIOA, &g);
    g.Pin = GPIO_PIN_6 | GPIO_PIN_7; /* PA6/PA7 TIM3 */
    g.Alternate = GPIO_AF2_TIM3;
    HAL_GPIO_Init(GPIOA, &g);
    g.Pin = GPIO_PIN_6 | GPIO_PIN_7; /* PB6/PB7 TIM4 */
    g.Alternate = GPIO_AF2_TIM4;
    HAL_GPIO_Init(GPIOB, &g);
    g.Pin = GPIO_PIN_6 | GPIO_PIN_7; /* PC6/PC7 TIM8 */
    g.Alternate = GPIO_AF4_TIM8;
    HAL_GPIO_Init(GPIOC, &g);

    encoder_one(&henc[0], TIM2);
    encoder_one(&henc[1], TIM3);
    encoder_one(&henc[2], TIM4);
    encoder_one(&henc[3], TIM8);
}

/* ------------------------------------------------------------------- adc */
static void adc_init(void) {
    __HAL_RCC_ADC12_CLK_ENABLE();
    GPIO_InitTypeDef g = {0};
    g.Mode = GPIO_MODE_ANALOG;
    g.Pull = GPIO_NOPULL;
    g.Pin = GPIO_PIN_0 | GPIO_PIN_1 | GPIO_PIN_2 | GPIO_PIN_3 | GPIO_PIN_4;
    HAL_GPIO_Init(GPIOC, &g);

    hadc1.Instance = ADC1;
    hadc1.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV4;
    hadc1.Init.Resolution = ADC_RESOLUTION_12B;
    hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
    hadc1.Init.ScanConvMode = ADC_SCAN_DISABLE;
    hadc1.Init.ContinuousConvMode = DISABLE;
    hadc1.Init.NbrOfConversion = 1;
    hadc1.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
    HAL_ADC_Init(&hadc1);
    HAL_ADCEx_Calibration_Start(&hadc1, ADC_SINGLE_ENDED);

    hadc2.Instance = ADC2;
    hadc2.Init = hadc1.Init;
    HAL_ADC_Init(&hadc2);
    HAL_ADCEx_Calibration_Start(&hadc2, ADC_SINGLE_ENDED);
    /* TODO(bench): move CS sampling to TIM1-triggered injected conversions so
     * samples land mid-PWM-pulse; software-triggered polling is the skeleton. */
}

static uint16_t adc_read(ADC_HandleTypeDef *h, uint32_t channel) {
    ADC_ChannelConfTypeDef c = {0};
    c.Channel = channel;
    c.Rank = ADC_REGULAR_RANK_1;
    c.SamplingTime = ADC_SAMPLETIME_47CYCLES_5;
    c.SingleDiff = ADC_SINGLE_ENDED;
    HAL_ADC_ConfigChannel(h, &c);
    HAL_ADC_Start(h);
    HAL_ADC_PollForConversion(h, 2);
    uint16_t v = (uint16_t)HAL_ADC_GetValue(h);
    HAL_ADC_Stop(h);
    return v;
}

/* ------------------------------------------------------------------ uart */
static void uart_init(void) {
    __HAL_RCC_USART2_CLK_ENABLE();
    GPIO_InitTypeDef g = {0};
    g.Pin = GPIO_PIN_2 | GPIO_PIN_3; /* PA2/PA3 -> ST-LINK VCP */
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    g.Alternate = GPIO_AF7_USART2;
    HAL_GPIO_Init(GPIOA, &g);

    huart2.Instance = USART2;
    huart2.Init.BaudRate = 921600;
    huart2.Init.WordLength = UART_WORDLENGTH_8B;
    huart2.Init.StopBits = UART_STOPBITS_1;
    huart2.Init.Parity = UART_PARITY_NONE;
    huart2.Init.Mode = UART_MODE_TX_RX;
    huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart2.Init.OverSampling = UART_OVERSAMPLING_16;
    HAL_UART_Init(&huart2);

    HAL_NVIC_SetPriority(USART2_IRQn, 6, 0);
    HAL_NVIC_EnableIRQ(USART2_IRQn);
    HAL_UART_Receive_IT(&huart2, &rx_byte, 1);
}

void USART2_IRQHandler(void) { HAL_UART_IRQHandler(&huart2); }

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *h) {
    if (h == &huart2) {
        uint16_t next = (uint16_t)((rx_head + 1) % RX_RING);
        if (next != rx_tail) { /* drop on overflow; parser resyncs */
            rx_ring[rx_head] = rx_byte;
            rx_head = next;
        }
        HAL_UART_Receive_IT(&huart2, &rx_byte, 1);
    }
}

/* Reception is a self-re-arming chain: the ONLY thing that arms the next byte
 * is HAL_UART_Receive_IT() at the end of the callback above. Break the chain
 * once and RX is dead for good, while TX keeps streaming telemetry - so the
 * MCU looks healthy and the Jetson looks at fault.
 *
 * HAL_UART_IRQHandler splits errors two ways (verified in the G4 HAL source,
 * stm32g4xx_hal_uart.c):
 *   FE / NE / PE  -> NON-blocking. Reception continues; nothing to do here.
 *   ORE / RTO     -> blocking. It calls UART_EndRxTransfer(), which disables
 *                    the RX interrupts, and then calls this callback. If this
 *                    is the default weak no-op, nothing ever re-arms.
 *
 * Only the overrun case is actually dangerous, and it could not be provoked
 * from the host (see devops/jetson/verify_uart_error_recovery.py): a 128 kB
 * flood at line rate never overran the ISR. The realistic sources are on-board
 * - a long higher-priority ISR, a critical section, or motor EMI on the cable
 * once the drivers are live. This is cheap insurance against a failure that
 * would otherwise be permanent and misattributed.
 */
void HAL_UART_ErrorCallback(UART_HandleTypeDef *h) {
    if (h != &huart2) return;
    rx_error_count++;
    __HAL_UART_CLEAR_OREFLAG(h);
    h->ErrorCode = HAL_UART_ERROR_NONE;
    /* Re-arm unconditionally: harmless if RX was never disabled (the
     * non-blocking case), essential if it was. */
    HAL_UART_Receive_IT(h, &rx_byte, 1);
}

/* SysTick is configured by HAL_Init(); required IRQ handler: */
void SysTick_Handler(void) { HAL_IncTick(); }

/* ------------------------------------------------------------- public api */
void hw_init(void) {
    HAL_Init();
    clock_init();
    gpio_init_all();
    pwm_init();
    encoders_init();
    adc_init();
    uart_init();
}

uint32_t hw_millis(void) { return HAL_GetTick(); }

void hw_set_motor(int wheel, int32_t duty_permille) {
    if (wheel < 0 || wheel > 3) return;
    if (duty_permille > 1000) duty_permille = 1000;
    if (duty_permille < -1000) duty_permille = -1000;
    GPIO_PinState a = (duty_permille > 0) ? GPIO_PIN_SET : GPIO_PIN_RESET;
    GPIO_PinState b = (duty_permille < 0) ? GPIO_PIN_SET : GPIO_PIN_RESET;
    HAL_GPIO_WritePin(BUDDY_INA_PORT[wheel], BUDDY_INA_PIN[wheel], a);
    HAL_GPIO_WritePin(BUDDY_INB_PORT[wheel], BUDDY_INB_PIN[wheel], b);
    uint32_t mag = (uint32_t)(duty_permille < 0 ? -duty_permille : duty_permille);
    uint32_t pulse = (htim1.Init.Period + 1u) * mag / 1000u;
    switch (wheel) {
    case 0: __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, pulse); break;
    case 1: __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, pulse); break;
    case 2: __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_3, pulse); break;
    default: __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_4, pulse); break;
    }
}

void hw_all_motors_off(void) {
    for (int i = 0; i < 4; i++) hw_set_motor(i, 0);
}

/* Sign is applied HERE, at the lowest layer, so every consumer above -
 * telemetry, the future velocity PID, the Jetson bridge - sees one convention:
 * positive counts mean the wheel is turning the way that drives the robot
 * forward. Left and right motors are mirrored on a skid-steer, so one side
 * counts down by geometry; negating in the harness instead would hide that
 * where nobody can see it. Values come from design_params.yaml. */
static const int8_t enc_sign[4] = BUDDY_ENCODER_SIGN;

int32_t hw_encoder_count(int wheel) {
    int32_t raw;
    if (wheel == 0) {
        raw = (int32_t)__HAL_TIM_GET_COUNTER(&henc[0]); /* 32-bit */
    } else {
        uint16_t now = (uint16_t)__HAL_TIM_GET_COUNTER(&henc[wheel]);
        int16_t delta = (int16_t)(now - enc_last[wheel]);
        enc_last[wheel] = now;
        enc_accum[wheel] += delta;
        raw = enc_accum[wheel];
    }
    return enc_sign[wheel] * raw;
}

uint16_t hw_motor_current_ma(int wheel) {
    /* VNH5019 CS: 140 mV/A. counts -> mV: *3300/4096; mV -> mA: *1000/140 */
    uint32_t counts = adc_read(&hadc1, BUDDY_CS_CHANNEL[wheel]);
    return (uint16_t)((counts * 3300u / 4096u) * 1000u / 140u);
}

uint16_t hw_vbat_mv(void) {
    uint32_t counts = adc_read(&hadc2, ADC_CHANNEL_5); /* PC4, 10:1 divider */
    return (uint16_t)(counts * 3300u / 4096u * 10u);
}

int hw_estop_active(void) {
    return HAL_GPIO_ReadPin(BUDDY_ESTOP_PORT, BUDDY_ESTOP_PIN) == GPIO_PIN_SET;
}

int hw_driver_fault(int wheel) {
    return HAL_GPIO_ReadPin(BUDDY_FAULT_PORT[wheel], BUDDY_FAULT_PIN[wheel]) ==
           GPIO_PIN_RESET; /* open-drain low = fault */
}

void hw_led(int on) {
    HAL_GPIO_WritePin(BUDDY_LED_PORT, BUDDY_LED_PIN,
                      on ? GPIO_PIN_SET : GPIO_PIN_RESET);
}

int hw_uart_read(uint8_t *buf, int maxlen) {
    int n = 0;
    while (n < maxlen && rx_tail != rx_head) {
        buf[n++] = rx_ring[rx_tail];
        rx_tail = (uint16_t)((rx_tail + 1) % RX_RING);
    }
    return n;
}

void hw_uart_write(const uint8_t *buf, int len) {
    HAL_UART_Transmit(&huart2, (uint8_t *)buf, (uint16_t)len, 20);
}
