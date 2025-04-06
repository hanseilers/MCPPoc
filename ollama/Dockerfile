FROM ollama/ollama:latest

# Create a directory for the startup script
WORKDIR /app

# Create a startup script that pulls the model and starts Ollama
RUN echo '#!/bin/bash\n\
    /bin/ollama serve &\n\
    sleep 5\n\
    echo "Pulling llama2 model..."\n\
    /bin/ollama pull llama2\n\
    echo "Model pulled successfully!"\n\
    # Keep the container running\n\
    tail -f /dev/null\n\
    ' > /app/start.sh && chmod +x /app/start.sh

# Set the startup script as the entrypoint
ENTRYPOINT ["/bin/bash", "/app/start.sh"]
