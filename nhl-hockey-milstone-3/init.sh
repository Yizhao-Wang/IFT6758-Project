if [ ! -d "results" ]; then
  echo "'results' directory does exist. Creating 'results' directory."
  mkdir results
  if [ $? -eq 0 ]; then
     echo "'results' directory created successfully."
  else
     echo "Error creating 'results' directory. Kindly take a look at the problem manually to fix it."
  fi
fi

if [ ! -d "/results/performance" ]; then
  echo "'results/performance' directory does exist. Creating 'results/performance' directory."
  mkdir "results/performance"
  if [ $? -eq 0 ]; then
     echo "'results/performance' directory created successfully."
  else
     echo "Error creating 'results/performance' directory. Kindly take a look at the problem manually to fix it."
  fi
fi

if [ ! -d "savedModels" ]; then
  echo "'savedModels' directory does exist. Creating 'savedModels' directory."
  mkdir savedModels
  if [ $? -eq 0 ]; then
     echo "'savedModels' directory created successfully."
  else
     echo "Error creating 'savedModels' directory. Kindly take a look at the problem manually to fix it."
  fi
fi
