# source me: userspace Intel GPU compute runtime (no root install)
export OCL_ICD_VENDORS=/home/sinkeat/Projects/graduation/android-masking/bench/neo/vendors
export LD_LIBRARY_PATH=/home/sinkeat/Projects/graduation/android-masking/bench/neo/root/usr/lib:/home/sinkeat/Projects/graduation/android-masking/bench/neo/root/usr/lib/intel-opencl${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export ZE_ENABLE_ALT_DRIVERS=/home/sinkeat/Projects/graduation/android-masking/bench/neo/root/usr/lib/libze_intel_gpu.so.1
