# Start from a Miniconda base image
FROM loudprepaire/gnina-api

RUN pip install  boto3


COPY run.py /workspace/run.py
COPY entrypoint.sh /workspace/entrypoint.sh

COPY . /workspace/
    
# Make the entrypoint script executable
RUN chmod +x /workspace/entrypoint.sh
RUN chmod +x /workspace/lib/gnina

ENTRYPOINT ["/workspace/entrypoint.sh"]