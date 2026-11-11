// Bring-up example: adapt these pins to the actual PCB before programming.
module prochip1504(input a, input b, output y);
//pragma attribute a pin_number 6
//pragma attribute b pin_number 8
//pragma attribute y pin_number 14
    assign y = a & b;
endmodule
