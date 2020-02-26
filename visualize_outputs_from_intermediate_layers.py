'''Visualize the outputs from intermediate layers for trained models'''
import argparse
import os
import utils
import model_handler as mh
import torch
from torchvision import transforms
from torch.autograd import Variable
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--image_path', default=os.path.join('data', 'test', 'no_label', '00109.jpg'),
                    help="Path of image to create visual")
parser.add_argument('--model_dir', default='experiments/base_model',
                    help="Directory containing params.json")


def input_number(message):
    while True:
        try:
            user_input = int(input(message))
        except ValueError:
            print("Please enter an integer! Try again.")
            continue
        else:
            return user_input
            break


class LayerActivations:
    features = None

    def __init__(self, model, layer_num):
        self.hook = list(model.children())[layer_num].register_forward_hook(self.hook_fn)

    def hook_fn(self, module, input, output):
        self.features = output.cpu().data.numpy()

    def remove(self):
        self.hook.remove()


def create_image_plot(activations, file_name):
    num_of_channels = activations.shape[1]
    fig = plt.figure(figsize=(20, 50))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=0.8, hspace=0.2, wspace=0.2)
    for i in range(num_of_channels):
        ax = fig.add_subplot(12, 5, i + 1, xticks=[], yticks=[])
        ax.imshow(activations[0][i])
    image_file = os.path.join(args.model_dir, file_name + ".png")
    fig.savefig(image_file)
    return image_file


if __name__ == '__main__':
    # Collect arguments from command-line options
    args = parser.parse_args()

    # Load the parameters from json file
    json_path = os.path.join(args.model_dir, 'params.json')
    assert os.path.isfile(
        json_path), "No json configuration file found at {}".format(json_path)
    params = utils.Params(json_path)

    # Set variables
    img_path = args.image_path
    model_name = params.model_name
    batch_size = params.test_batch_size
    num_workers = params.num_workers

    # Detect if we have a GPU available
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    # Load model
    print('Loading model...')
    model_ft = mh.load_checkpoint(filepath=args.model_dir, device=device)

    # Get the required input size of the network for resizing images
    input_size = mh.input_size_of_model(model_name)

    # Data augmentation and normalization image
    data_transforms = transforms.Compose([
        transforms.Resize(input_size),
        transforms.CenterCrop(input_size),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    img_pil = Image.open(img_path)
    image_tensor = data_transforms(img_pil).float()
    image_tensor = image_tensor.unsqueeze_(0)
    input_img = Variable(image_tensor)
    input_img = input_img.to(device)

    layer = input_number('Enter the number of the layer to visualize (0 to num of layers): ')

    # View layer
    print('Creating image...')
    convolution_out = LayerActivations(model_ft.features, layer)
    output = model_ft(Variable(input_img))
    convolution_out.remove()
    activations = convolution_out.features
    print(activations.shape[1])
    vis_saved = create_image_plot(activations, 'vis_of_layer_{}'.format(layer))

    print('Done. Visualization saved to: {}'.format(vis_saved))
