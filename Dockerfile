FROM ollama/ollama 
RUN ollama serve & sleep 5 &&  ollama pull nomic-embed-text-v2-moe:latest && pkill ollama 
CMD ["serve"]