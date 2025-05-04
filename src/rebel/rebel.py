from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch
from tqdm import tqdm
import signal
import threading

print("START: loading models", flush=True)
tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")
print("DONE: loading models", flush=True)

def extract_triplets(text):
    triplets = []
    relation, subject, relation, object_ = '', '', '', ''
    text = text.strip()
    current = 'x'
    for token in text.replace("<s>", "").replace("<pad>", "").replace("</s>", "").split():
        if token == "<triplet>":
            current = 't'
            if relation != '':
                triplets.append({'head': subject.strip(), 'type': relation.strip(),'tail': object_.strip()})
                relation = ''
            subject = ''
        elif token == "<subj>":
            current = 's'
            if relation != '':
                triplets.append({'head': subject.strip(), 'type': relation.strip(),'tail': object_.strip()})
            object_ = ''
        elif token == "<obj>":
            current = 'o'
            relation = ''
        else:
            if current == 't':
                subject += ' ' + token
            elif current == 's':
                object_ += ' ' + token
            elif current == 'o':
                relation += ' ' + token
    if subject != '' and relation != '' and object_ != '':
        triplets.append({'head': subject.strip(), 'type': relation.strip(),'tail': object_.strip()})
    return triplets


def infer_batch(batch, model, tokenizer):
    output_tokens = model.generate(
        input_ids = batch.to(model.device),
        attention_mask = torch.ones_like(batch).to(model.device)
    )
    sentenses = tokenizer.batch_decode(output_tokens)
    return sentenses
def extract_knowledge_graph(
    text: str,
    span_length: int,
    batch_size: int,
    device = torch.device('cpu'),
    prog_bar: bool = False,
    timeout_minutes: int = 5,
    silent = True
):
    if silent:
        global print
        print = lambda *args, **kwargs: None
    print("START: loading models", flush=True)
    model.to(device)
    print(f"model device: {model.device}", flush=True)
    print("DONE: loading models", flush=True)
    print("START: tokenizing input", flush=True)
    tokens = tokenizer(text, return_tensors='pt')
    print("DONE: tokenizing input", flush=True)
    input_ids = tokens['input_ids'].squeeze()
    input_ids
    num_spans = input_ids.shape[0]//span_length
    reshaped_input_ids = input_ids[:num_spans*span_length].reshape(num_spans, span_length)
    num_batches = reshaped_input_ids.shape[0]//batch_size
    batched_inputs = reshaped_input_ids[:num_batches*batch_size, :span_length].reshape(num_batches, batch_size, span_length)
    iterator = tqdm if prog_bar else iter
    print("START: knowledge graph extration", flush=True)
    relations = []
    timed_out=False
    def trigger_timeout():
        nonlocal timed_out
        timed_out = True
    timer = threading.Timer(timeout_minutes*60, trigger_timeout)
    timer.start()
    # def timeout(*args):
    #     raise TimeoutError("Knowledge Graph Extration timed out")
    # signal.signal(signal.SIGALRM, timeout)
    # signal.alarm(timeout_minutes*60)
    try:
        for batch in iterator(batched_inputs):
            if timed_out: raise TimeoutError("Knowledge Graph Extration timed out")
            sentenses = infer_batch(batch, model, tokenizer)
            for sentense in sentenses:
                triplets = extract_triplets(sentense)
                relations.extend(triplets)
        # signal.alarm(0)
        print("DONE: knowledge graph extration", flush=True)
    except (Exception, KeyboardInterrupt, TimeoutError) as e:
        print(f"ERROR: {e}", flush=True)
        print("INTERUPTED: knowledge graph extration", flush=True)
        pass
    finally:
        timer.cancel()
    print("START: make knowledge graph table", flush=True)
    kb = set()
    for link in relations:
        kb.add((link['head'], link['type'], link['tail']))
    print("DONE: make knowledge graph table", flush=True)
    return kb

    

def make_kb(text, **kwargs):

    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
    model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")
    gen_kwargs = {
        "max_length": 256,
        "length_penalty": 0,
        "num_beams": 3,
        "num_return_sequences": 3,
    }
    gen_kwargs.update(kwargs)

    # Text to extract triplets from
    # text = 'Punta Cana is a resort town in the municipality of Higüey, in La Altagracia Province, the easternmost province of the Dominican Republic.'

    # Tokenizer text
    model_inputs = tokenizer(text, max_length=gen_kwargs['max_length'], padding=True, truncation=True, return_tensors = 'pt')

    # Generate
    generated_tokens = model.generate(
        model_inputs["input_ids"].to(model.device),
        attention_mask=model_inputs["attention_mask"].to(model.device),
        **gen_kwargs,
    )

    # Extract text
    decoded_preds = tokenizer.batch_decode(generated_tokens, skip_special_tokens=False)

    kb = set()
    for sentence in decoded_preds:
        for link in extract_triplets(sentence):
            kb.add((link['head'], link['type'], link['tail']))
    # Extract triplets
    # for idx, sentence in enumerate(decoded_preds):
    #     print(f'Prediction triplets sentence {idx}')
    #     print(extract_triplets(sentence))

    return kb
