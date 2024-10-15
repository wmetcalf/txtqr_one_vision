# txtqr_one_vision
Tries to perform QR extraction from txt/html and msg/eml bodies

#Install
```
pip3 install git+https://github.com/wmetcalf/txtqr_one_vision.git
```

#Usage
```
txtqr_one_vision --help
usage: txtqr_one_vision [-h] -i INPUT [--decoder {bft_qr_reader,none,zxing}] [-o OUTPUT] [--model_dir MODEL_DIR] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

ASCII/Unicode EML/HTML/TXT/MSG QRCode Seek and Destroy https://www.youtube.com/watch?v=FLTchCiC0T0

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input file or directory
  --decoder {bft_qr_reader,none,zxing}
                        Decoder to use (bft_qr_reader or zxing) or none
  -o OUTPUT, --output OUTPUT
                        Output directory
  --model_dir MODEL_DIR
                        Path to wechat model dir
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level. Default is DEBUG.
```
