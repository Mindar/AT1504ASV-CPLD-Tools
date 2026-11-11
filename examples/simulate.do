# Run with the examples directory as cwd, or copy these three files together.
onerror {quit -code 1 -force}
onbreak {quit -code 1 -force}
vlib work
vlog logic.v logic_tb.v
vsim work.logic_tb
run 100 ns
quit -code 0 -force
