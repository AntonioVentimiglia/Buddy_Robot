/* Pin map for the drive MCU — code mirror of docs/pin_map.md.
 * Wheel index order everywhere: 0=LF, 1=LR, 2=RF, 3=RR (protocol order).
 * Change this file and docs/pin_map.md together. */
#ifndef PINS_H
#define PINS_H

#include "stm32g4xx_hal.h"

/* VNH5019 direction pins */
static GPIO_TypeDef *const BUDDY_INA_PORT[4] = {GPIOB, GPIOB, GPIOB, GPIOB};
static const uint16_t BUDDY_INA_PIN[4] = {GPIO_PIN_0, GPIO_PIN_2, GPIO_PIN_4,
                                          GPIO_PIN_13};
static GPIO_TypeDef *const BUDDY_INB_PORT[4] = {GPIOB, GPIOB, GPIOB, GPIOB};
static const uint16_t BUDDY_INB_PIN[4] = {GPIO_PIN_1, GPIO_PIN_10, GPIO_PIN_5,
                                          GPIO_PIN_14};

/* VNH5019 EN/DIAG fault inputs (pull-up; low = fault) */
static GPIO_TypeDef *const BUDDY_FAULT_PORT[4] = {GPIOC, GPIOC, GPIOC, GPIOD};
static const uint16_t BUDDY_FAULT_PIN[4] = {GPIO_PIN_10, GPIO_PIN_11,
                                            GPIO_PIN_12, GPIO_PIN_2};

/* VNH5019 CS -> ADC1 channels (PC0..PC3 = IN6..IN9) */
static const uint32_t BUDDY_CS_CHANNEL[4] = {ADC_CHANNEL_6, ADC_CHANNEL_7,
                                             ADC_CHANNEL_8, ADC_CHANNEL_9};

/* E-stop chain state (reporting only; hardware cuts motor power upstream) */
#define BUDDY_ESTOP_PORT GPIOB
#define BUDDY_ESTOP_PIN GPIO_PIN_12

/* Nucleo LD2 */
#define BUDDY_LED_PORT GPIOA
#define BUDDY_LED_PIN GPIO_PIN_5

#endif /* PINS_H */
