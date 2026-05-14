<<<<<<< HEAD
import torch
from transformers import LEDTokenizer, LEDForConditionalGeneration

MODEL_PATH = "legal_led_model"

tokenizer = LEDTokenizer.from_pretrained(MODEL_PATH)
model = LEDForConditionalGeneration.from_pretrained(MODEL_PATH)

model.eval()

text = "This is a legal agreement between two parties regarding property dispute."

inputs = tokenizer(text, return_tensors="pt")

global_attention_mask = torch.zeros_like(inputs["input_ids"])
global_attention_mask[:, 0] = 1

with torch.no_grad():
    output = model.generate(
        input_ids=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        global_attention_mask=global_attention_mask,
        max_new_tokens=50
    )

=======
import torch
from transformers import LEDTokenizer, LEDForConditionalGeneration

MODEL_PATH = "legal_led_model"

tokenizer = LEDTokenizer.from_pretrained(MODEL_PATH)
model = LEDForConditionalGeneration.from_pretrained(MODEL_PATH)

model.eval()

text = "This is a legal agreement between two parties regarding property dispute."

inputs = tokenizer(text, return_tensors="pt")

global_attention_mask = torch.zeros_like(inputs["input_ids"])
global_attention_mask[:, 0] = 1

with torch.no_grad():
    output = model.generate(
        input_ids=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        global_attention_mask=global_attention_mask,
        max_new_tokens=50
    )

>>>>>>> 273dcd41279759bf77f4e5d4c52464f035c48e21
print(tokenizer.decode(output[0], skip_special_tokens=True))