# Texture customization (advanced)

![](../img/customized_uv_groups.png)

You can customize the appearance of a UV-group by applying masks to its faces
in new custom panel in [Scene Properties](../gui_changes/#scene-properties).

Masks are filters that are applied to the texture when it is generated.
Each UV-group has 6 faces. You can switch between faces to edit with
"Side:" dropdown menu. The image below shows how the names of the
sides (side1-6) are corelated to their placement on the texture.

![](../img/faces.png)

New masks are added with "Add mask" dropdown menu. There are 8 different types
of masks.


!!! note

    All masks have an eye icon in the upper right corner that can be used to
    temporarily disable / enable the mask.

## Color Palette Mask
![](../img/color_palette_mask.png)

This mask takes the grayscale image as an input and maps its brightness values
to a color image with a palette defined as a list of colors.

Properties:

- Colors - list of colors in the palette
- Interpolate - whether there should be a smooth transition between the colors
    on the palette.
- Normalize - normalizes the input values so that the whole color palette is
    used.

!!! note

    When input image is not grayscale than it gets converted to grayscale
    before applying the mask.

!!! note

    Color palette mask is the only mask which can't be used inside the Mix
    Mask. If you put this mask into mix mask it will have no effect.



## Gradient Mask
![](../img/gradient_mask.png)

The Gradient mask creates a grayscale gradient with stripes of varying darkness
and width. The direction in which the stripes are drawn is defined with two
points on the texture. The grayscale image is than multiplied by the input image.

Properties:

- Point A - the starting point of drawing gradient stripes.
- Point B - the end point of drawing gradient stripes.
- Relative boundaries - whether points A and B should be passed as absolute
    values (number of pixels from the lower left corner of the texture) or as a
    fraction of the texture size (0.0 lower left corner, 1.0 upper right corner).
    The absolute values can be negative, meaning they represent the number of
    pixels from the top right corner (starting at -1).
- Stripes - the list of stripes in the gradient their colors (strengths) and
    their widths. The widths define their placement on a line between points
    A and B so in most cases the width of the first stripe is 0, which means
    that this stripe should be drawn at the Point A.
- Exponent - the filter image is raised to the power of this value before it
    is multiplied by the image.
## Ellipse Mask
![](../img/ellipse_mask.png)

Ellipse mask creates a grayscale image of ellipse that fits between Point A and
Point B. The grayscale image is than multiplied by the input image.

Properties:

- Point A and B - boundaries of the ellipse.
- Relative boundaries - whether points A and B should be passed as absolute
    values (number of pixels from the lower left corner of the texture) or as a
    fraction of the texture size (0.0 lower left corner, 1.0 upper right corner).
    The absolute values can be negative, meaning they represent the number of
    pixels from the top right corner (starting at -1).
- Exponent - the filter image is raised to the power of this value before it
    is multiplied by the image.
- Strength - the min and max values of brightness of created filter image.
- Hard edge - whether the ellipse should have hard edges or the brightness
    of the inner part of the ellipse should be smoothly interpolated to 
    the edges of the image.



## Rectangle Mask
![](../img/rectangle_mask.png)

Rectangle mask creates a grayscale image of rectangle between Point A and
Point B. The grayscale image is than multiplied by the input image.

Properties:

- Point A and B - opposite corners of the rectangle.
- Relative boundaries - whether points A and B should be passed as absolute
    values (number of pixels from the lower left corner of the texture) or as a
    fraction of the texture size (0.0 lower left corner, 1.0 upper right corner).
    The absolute values can be negative, meaning they represent the number of
    pixels from the top right corner (starting at -1).
- Exponent - the filter image is raised to the power of this value before it
    is multiplied by the image.
- Strength - the min and max values of brightness of created filter image.
- Hard edge - whether the rectangle should have hard edges or the brightness
    of the inner part of the rectangle should be smoothly interpolated to 
    the edges of the image.




## Stripes Mask
![](../img/stripes_mask.png)

Rectangle mask creates a grayscale image with repeating stripes of certain
width and brightness. The grayscale image is than multiplied by the input
image.

Properties:

- Relative boundaries - whether the width of the stripes is expressed as a
    fraction of the image width / height.
- Stripes - the list of the stripes, their width and their brightness.
- Horizontal - whether the stripes should be vertical or horizontal.




## Random Mask
![](../img/random_mask.png)

Random mask creates a grayscale image with randomly bright pixels. The
grayscale image is than multiplied by the input image.

- Exponent - the filter image is raised to the power of this value before it
    is multiplied by the image.
- Strength - the min and max brightness values of the pixels on the filter
    image.
- Use seed - allows you to set the seed for the color randomization.



## Color Mask
![](../img/color_mask.png)

Color mask multiplies the input mask by a color.




## Mix Mask
![](../img/mix_mask.png)

Mix mask lets you mix multiple masks in different way than just default
multiplication. 

Properties:

- Exponent - the filter image is raised to the power of this value before it
    is multiplied by the image.
- Strength - the min and max values of the brightness of returned filter image.
    The filter image brightness values are mapped to fit on the scale between
    values defined with "strength"
- Mix mode - how to mix filter images produced by other masks. There are 4
    options: min, max, mean and median.
- Number of children - Number of mixed masks.

!!! note

    Mix mask ignores the color palette masks because color palette mask does
    not create a filter image (it just alters the image from the input).