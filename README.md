# minimalBlur

This is a short working example of face blurring that seems to produce far less double-jpg'ing artifacts in regions that are not blurred compared to alternate methods. This script is *not* meant as a turnkey solution to be used for other projects, but rather is a demonstration for developers to re-purpose. I'm posting this in the hopes that it is useful, but will not be monitoring github issues.

If you want to use this in your own project, I'd suggest pulling out the following two functions:
- blur (which is based on Kaiyu Yang's version here: https://github.com/princetonvisualai/imagenet-face-obfuscation/blob/main/experiments/blurring.py)
- handle(...), which demonstrates how to mitigate double jpg'ing. handle is also a few small modifications away from being able to be easily parallelized with multiprocessing

Do *not* use:
- handleBad -- this demonstrates a data processing that causes double jpging artifacts.

You can try the script on either calder.jpg or crop5.jpg. The script will generate the blurred version. If showDiff is set to true, the script will also generate a version that does not try to avoid double jpg'ing artifacts as well as generate difference maps.

Dependencies:
- Python Image Library
- Numpy 
