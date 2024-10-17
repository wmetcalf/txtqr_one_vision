# txtqr_one_vision
Tries to perform QR extraction from txt/html and msg/eml bodies

#Install base package
```
pip3 install git+https://github.com/wmetcalf/txtqr_one_vision.git
```

#Install base and optional dependencies 
```
pip3 install git+https://github.com/wmetcalf/txtqr_one_vision.git#egg=txtqr_one_vision[decoders,email,magika]
```

#Usage as class you can input a file path or bytes and optionally override the class defined outputdir for calls to seek_and_destroy

```
from txtqr_one_vision import QRCodeTXTExtractor
ov = QRCodeTXTExtractor('/tmp/ironeagle/', None, decoder='none')
with open('/home/coz/Downloads/Office365 Secure Doc.txt','rb') as f:
     print(ov.seek_and_destroy(f.read(),True,'/tmp/ironeagle2_the_search_for_more_eagles/'))
 
{'file': '/tmp/ironeagle2_the_search_for_more_eagles/tmpdbprfjdb', 'mime_type': 'text/plain', 'qrcode_images': ['/tmp/ironeagle2_the_search_for_more_eagles/f51e0cdd-e1c3-4d60-a48f-2dc41a8f3f0c.png'], 'decoding_results': [], 'errors': []}
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
