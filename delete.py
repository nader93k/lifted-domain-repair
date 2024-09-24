import os
import logging

def process_folders(folder_list):

    for folder in folder_list:
        # Change the log file for each folder
        log_file = os.path.join(folder, 'folder_operations.log')
        
        logging.basicConfig(file=log_file)

        try:
            # Your processing logic here
            logger.info(f"Processing folder: {folder}")
            
            # Example operations
            files = os.listdir(folder)
            logger.debug(f"Files in folder: {files}")

            # Simulate some operations
            for file in files:
                logger.info(f"Operating on file: {file}")
                # Your file operation logic here

        except Exception as e:
            logger.error(f"An error occurred while processing folder {folder}: {str(e)}")

    # Clean up the last file handler after processing all folders
    if file_handler:
        logger.removeHandler(file_handler)
        file_handler.close()

# List of folders to process
folders_to_process = [
    '/path/to/folder1',
    '/path/to/folder2',
    '/path/to/folder3'
]



logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filemode='w')
# Run the process
process_folders(folders_to_process)