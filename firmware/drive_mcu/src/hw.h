/* Hardware layer for the drive MCU — all HAL/peripheral access lives here.
 *
 * Pin assignments: docs/pin_map.md, mirrored in include/pins.h.
 * Everything above this layer (state_machine.c, protocol) is pure C and
 * host-tested; this file is only exercised on the target.
 */
#ifndef HW_H
#define HW_H

#include <stdint.h>

/* Wheel index order everywhere: 0=LF, 1=LR, 2=RF, 3=RR (protocol order). */

void hw_init(void); /* clocks 170 MHz, GPIO, TIM1 PWM, encoder timers, ADC, UART */

uint32_t hw_millis(void);

/* Motor output: signed duty in [-1000, 1000]; gate with sm_motion_allowed().
 * Sets INA/INB direction pins and TIM1 compare. duty 0 = brake low. */
void hw_set_motor(int wheel, int32_t duty_permille);
void hw_all_motors_off(void);

/* Sensors */
int32_t hw_encoder_count(int wheel);   /* accumulated quadrature count */
uint16_t hw_motor_current_ma(int wheel); /* from VNH5019 CS via ADC */
uint16_t hw_vbat_mv(void);
int hw_estop_active(void);             /* PB12 chain state, 1 = E-stop pressed */
int hw_driver_fault(int wheel);        /* EN/DIAG pulled low by driver */

/* Status LED heartbeat */
void hw_led(int on);

/* UART (VCP): non-blocking ring-buffer RX, blocking TX for the skeleton. */
int hw_uart_read(uint8_t *buf, int maxlen); /* returns bytes read */
void hw_uart_write(const uint8_t *buf, int len);

#endif /* HW_H */
