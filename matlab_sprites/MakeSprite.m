function [sprite,n] = MakeSprite(Vol,fname,color,threshold)
% Make a sprite / Mosaic from a 3D volume, for use with BrainSprite html
% viewer. 
%
% Inputs: MakeSprite(Vol,fname,color)
% 
%  Vol   = the 3D volume
%  fname = the file savename
%  color = 'bw' (default) or 'overlay' - if this is to be a b&w (structural
%  MRI) image or a functional overlay.
%
%  Optional 4th input: threshold as % of maximum, between [0,1], def = 0.5
%  for alpha
%
% AS

if nargin < 2
    write = 0;
else
    write = 1;
end

if nargin < 3 || isempty(color)
    color = 'bw';
end

if nargin < 4 || isempty(threshold)
    threshold = 0.5;
end

% dimensions, downsampling
S   = size(Vol);
ds  = ceil(S / 192);
Vol = Vol(ds(1):ds(1):end,ds(2):ds(2):end,ds(3):ds(3):end);
S   = size(Vol);

% initially generate one long image
Img = [];
for i = 1:S(1)
    switch color
        case 'bw'
            slice = mat2gray( flipud( ( squeeze(Vol(i,:,:)) )') );
        case 'overlay'
            slice =         ( flipud( ( squeeze(Vol(i,:,:)) )') );
    end
    Img   = [Img slice];
end
    
% then reshape - be lazy and force 8 * n
nv  = S(2)/8;
ons = (S(1)*8:S(1)*8:S(1)*nv*8) - ( S(1)*8 - 1);
ofs = (S(1)*8:S(1)*8:S(1)*nv*8);

sprite = [];
for i = 1:length(ons)
    sprite = [sprite; Img(:,ons(i):ofs(i))];
end

n = [S(1) S(2)];

% write it out
if write
    if isempty(fname)
        fname = 'MySprite';
    end
    switch color
        case 'bw'
            imwrite(sprite,[fname '.png']);
        case 'overlay'
            RGB = makecolbar(sprite(:),cmocean('balance'));
            RGB = reshape(RGB,[size(sprite,1),size(sprite,2),3]);     
            Maxi  = max(abs(sprite(:)));
            Alphs = abs(sprite);
            Alphs(Alphs < Maxi*threshold) = 0;
            imwrite(RGB,[fname '.png'],'Alpha',Alphs);
    end
            
end