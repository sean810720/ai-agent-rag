<p align="center"><h1>A digital doctor with RAG and LLM</h1></p>
<div width="100%">
    <span style="float:left;"><img width="49%" src="./img/index.png"></span>
    <span style="float:left;"><img width="49%" src="./img/index.gif"></span>
</div>
<br/>

## Technique Stacks
- Langchain
- Gradio
- Firebase Realtime Database
- Groq Llama3-8B
- OpenAI Embedding
<br/>

## Methodology
Native RAG with similarity threshold limit
<br/>
<br/>

## Platform Support
- OS X 10.11 (x86_64)
- Other Linux-like OS
<br/>

## How to Build

### (0) Get Groq API key
At first, register a free Groq account and get the API key from here：<br/>
<a href="https://console.groq.com/login" target="_blank">https://console.groq.com/login</a>
<br/>

### (1) Install requirements
```
pip3 install -r requirements.txt
```

### (2) Edit config.ini
```
mv ./config.ini.example ./config.ini
```
Then update required "api_key" in the content of config.ini
<br/>
<br/>

## How to Run
```
python3 ./ai-doctor.py
```
It will deploy a local web server at: http://127.0.0.1:7860, just run it on your browser.
