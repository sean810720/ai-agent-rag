<p align="center"><h1>A digital doctor with RAG and LLM</h1></p>
<div width="100%">
    <span style="float:left;"><img width="49%" src="./img/index.png"></span>
    <span style="float:left;"><img width="49%" src="./img/index.gif"></span>
</div>
<br/>

## Platform Support
- OS X 10.11 (x86_64)
- Other Linux-like OS

## How to Build

### (1) Install requirements
```
pip3 install -r requirements.txt
```

### (2) Edit config.ini
```
mv ./config.ini.example ./config.ini
```
And then update "api_key" in content of config.ini


## Run
```
python3 ./ai-doctor.py
```
It will deploy a service with url: http://127.0.0.1:7860, just run it on your browser.
