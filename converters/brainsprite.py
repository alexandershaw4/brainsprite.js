# Christian Dansereau 2016 Copyright
import os
import numpy as np
import nibabel as nib
from PIL import Image
import json
from nilearn.image import resample_img


def load_json_template():
    data_file = '{ \
    "canvas": "3Dviewer",\
    "sprite": "spriteImg",\
    "flagCoordinates": true,\
    "nbSlice": {\
        "Y": 233,\
        "Z": 189\
    },\
    "colorBackground": "#000",\
    "colorFont": "#FFF",\
    "overlay": {\
        "sprite": "overlayImg",\
        "nbSlice": {\
            "Y": 233,\
            "Z": 189\
        },\
        "opacity": 0.7\
    },\
    "colorMap": {\
        "img": "colorMap",\
        "min": 0.2,\
        "max": 0.66\
    }\
    }'

    data = json.loads(data_file)
    return data


def make_folder(path, directory):
    if not os.path.exists(path + directory):
        os.makedirs(path + directory)


def loadVolume(source_file):
    img = nib.load(source_file)
    vol = img.get_data()

    # check if its a nii file
    ext = getExt(source_file)
    if ext == ".nii":
        vol = np.swapaxes(vol, 0, 2)
    return vol


def getspec(vol):
    nx, ny, nz = vol.shape
    nrows = int(np.ceil(np.sqrt(nz)))
    ncolumns = int(np.ceil(nz / (1. * nrows)))
    return nrows, ncolumns, nx, ny, nz


def getExt(source_file):
    # Getting the extension
    if os.path.splitext(source_file)[1] == '.gz':
        extension = os.path.splitext(os.path.splitext(source_file)[0])[1]
    else:
        extension = os.path.splitext(source_file)[1]

    return extension


def montage(vol):
    nrows, ncolumns, nx, ny, nz = getspec(vol)

    mosaic = np.zeros((nrows * nx, ncolumns * ny))
    indx, indy = np.where(np.ones((nrows, ncolumns)))

    for ii in range(vol.shape[2]):
        # we need to flip the image in the x axis
        mosaic[(indx[ii] * nx):((indx[ii] + 1) * nx), (indy[ii] * ny):((indy[ii] + 1) * ny)] = vol[::-1, :, ii]

    return mosaic


def saveMosaic(mosaic, output_path, overlay=False, overlay_threshold=0.1):
    if overlay:
        mosaic[mosaic < overlay_threshold] = 0
        im = Image.fromarray(np.uint8(plt.cm.hot(mosaic) * 255))
        mask = Image.fromarray(np.uint8(mosaic > 0) * 255).convert("L")
        im.putalpha(mask)
    else:
        im = Image.fromarray(mosaic).convert('RGB')
    # if im.mode != 'RGBA':
    #    im = im.convert('RGBA')
    im.save(output_path)


def transform_package(img_path, output_folder, overlay_path=''):
    if overlay_path == '':
        transform(img_path, output_folder + 'bkg_mosaic.jpg', output_folder + 'params.js')
    else:
        transform(img_path, output_folder + 'bkg_mosaic.jpg', output_folder + 'params.js', overlay_path,
                  output_folder + 'overlay_mosaic.png')


def transform(source_bkg_path, out_bkg_path, out_json, source_overlay_path='', out_overlay_path='',
              overlay_threshold=0.1):
    # load data
    bkg_vol = loadVolume(source_bkg_path)
    bkg_vol = (bkg_vol / float(bkg_vol.max())) * 255.

    # populate json
    params = load_json_template()
    params['nbSlice']['Y'] = bkg_vol.shape[1]
    params['nbSlice']['Z'] = bkg_vol.shape[0]

    # make bkg montage save
    mosa_bkg = montage(bkg_vol)
    saveMosaic(mosa_bkg, out_bkg_path)

    if source_overlay_path != '':
        # load data
        bkimg = nib.load(source_bkg_path)
        overimg = nib.load(source_overlay_path)

        # transform slice order and resample to fit bkimg
        # check if its a nii file
        ext = getExt(source_overlay_path)
        ext_bkg = getExt(source_bkg_path)
        if ext == ".nii":
            if ext_bkg == ".mnc":
                bkimg.affine[:, [0, 2]] = bkimg.affine[:, [2, 0]]
            overimg = resample_img(overimg, bkimg.affine, bkimg.shape[::-1], interpolation='nearest')
            overlay_vol = np.swapaxes(overimg.get_data(), 0, 2)
        else:
            overimg = nib.nifti1.Nifti1Image(overimg.get_data(), overimage.get_affine)
            overimg = resample_img(overimg, bkimg.affine, bkimg.shape)
            overlay_vol = overimg.get_data()

        # populate json
        params['overlay']['nbSlice']['Y'] = overlay_vol.shape[1]
        params['overlay']['nbSlice']['Z'] = overlay_vol.shape[0]
        # make overlay montage and save
        mosa_overlay = montage(overlay_vol)
        saveMosaic(mosa_overlay, out_overlay_path, overlay=True, overlay_threshold=overlay_threshold)
    else:
        del params['overlay']

    del params['colorMap']
    if out_json[-3:] == '.js':
        with open(out_json, 'w') as outfile:
            data = "var jsonParams = '" + json.dumps(params) + "';"
            outfile.write(data)
    else:
        with open(out_json, 'w') as outfile:
            data = json.dumps(params)
            outfile.write(data)


def test_mosaic():
    # custom path
    background = "test_anat.mnc.gz"
    overlay = "DMN.nii.gz"
    output_folder = "/home/cdansereau/virenv/"
    #background = "t2.nii.gz"
    #overlay = "t2_seg.nii.gz"
    #output_folder = "/home/cdansereau/t2/"
    # transform data
    transform(output_folder + background, output_folder + 'bkg_mosaic.jpg', output_folder + 'params.json',
              output_folder + overlay, output_folder + 'overlay_mosaic.png', overlay_threshold=0.3)