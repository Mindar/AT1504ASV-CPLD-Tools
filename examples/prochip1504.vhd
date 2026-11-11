-- Bring-up example: adapt these pins to the actual PCB before programming.
library ieee;
use ieee.std_logic_1164.all;

entity prochip1504 is
    port (a, b : in std_logic; y : out std_logic);
    attribute pin_number : string;
    attribute pin_number of a : signal is "6";
    attribute pin_number of b : signal is "8";
    attribute pin_number of y : signal is "14";
end entity;

architecture rtl of prochip1504 is
begin
    y <= a and b;
end architecture;
