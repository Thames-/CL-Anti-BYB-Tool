# CL-Anti-BYB-Tool
Handy amateur tool for flagging CL posts from backyard breeders. Currently specific to pitbulls / bully breeds.

## Getting Started

1. create virtual environment  
   
   In your project directory:  
   ```python -m venv venv_name```

This only needs to be done once.
   
3. Install requirements.txt  

  ```pip install -r requirements.txt```

This only needs to be done once.
  
3. Populate 'searches.txt' with URLs from r/puppysearch  

  Each URL should be on its own line. See the file for example URLs.
   
4. Activate virtual environment.

   In terminal, navigate to your project directory. Then enter the following:

  On Windows:  
  ```venv_name\Scripts\activate.bat```  

  On Unix or MacOS, run:  
  ```source venv_name/bin/activate```  

5. Run the python script  

   ```python3 noBYB.py```
