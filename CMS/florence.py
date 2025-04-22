"""
Author: Ansh Mathur
Github: github.com/Fakesum
Repo: github.com/Thinkodes/CMS
"""
import time
import cv2
import torch
from PIL import Image
import os
from transformers import AutoModelForCausalLM, AutoProcessor

from .utils import logger

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

FLORENCE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Florence-2-base-ft")

if "CMS_ACTIVE" in os.environ:
    florence_model = AutoModelForCausalLM.from_pretrained(
        FLORENCE_PATH,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        trust_remote_code=True,
        local_files_only=True
    ).to(device)
    florence_processor = AutoProcessor.from_pretrained(FLORENCE_PATH, trust_remote_code=True, local_files_only=True)

# Function to measure response time and return generated text
def florence_endpoint(cv2_image, prompts: list[str]) -> list[str]:
    global florence_model, florence_processor
    # Load the model and processor

    logger.info("starting processing by florence.")

    # Convert CV2 image (BGR) to PIL image (RGB)
    image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)

    results = []

    for prompt in prompts:
        # Prepare inputs
        inputs = florence_processor(text=prompt, images=image, return_tensors="pt").to(device, 
                                                                                    torch.float16 if torch.cuda.is_available() else torch.float32)

        # Measure time taken for generation
        start_time = time.time()
        generated_ids = florence_model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=1024,
            do_sample=False,
            num_beams=3
        )
        end_time = time.time()

        # Decode the generated text
        generated_text = florence_processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        parsed_answer = florence_processor.post_process_generation(generated_text, task=prompt, image_size=(image.width, image.height))

        # Calculate time taken
        time_taken = end_time - start_time
        logger.debug(f"Time Taken for florence({prompt}): {time_taken}")
        logger.debug(f"Answer from florence({prompt}): {parsed_answer[prompt]}")
        results.append(parsed_answer[prompt])
    return results