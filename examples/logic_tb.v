`timescale 1ns/1ps
module logic_tb;
    reg a;
    reg b;
    wire y;
    integer i;
    logic_gate dut(.a(a), .b(b), .y(y));
    initial begin
        for (i = 0; i < 4; i = i + 1) begin
            {a, b} = i;
            #10;
            if (y !== (a & b)) begin
                $display("TEST_FAIL: input %d", i);
                $stop;
            end
        end
        $display("TEST_PASS: all four AND-gate input combinations");
        // No $finish: let the DO script control the process exit code.
    end
endmodule
