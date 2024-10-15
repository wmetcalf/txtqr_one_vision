from setuptools import setup, find_packages

setup(
    name='txtqr_one_vision',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'opencv-python',
        'opencv-contrib-python',
        'python-magic',
        'pillow',
        'python-multipart',
        'magika',
        "msg_parser",
        "beautifulsoup4",
        "zxing-cpp"
    ],
    extras_require={
        'decoders': [
            'bft_qr_reader @ https://github.com/wmetcalf/bft_qr_reader.git',
            ]
    },    
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'txtqr_one_vision=txtqr_one_vision.txtqr_one_vision:main',
        ],
    },
    author='Will Metcalf',
    author_email='william.metcalf@gmail.com',
    description='txt/html/e-mail qr code to png',
    url='https://github.com/wmetcalf/txtqr_one_vision',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)

