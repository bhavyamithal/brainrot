# Content Templates Guide

Templates define the visual style of generated videos. This guide explains how to use built-in templates and create custom ones.

## Built-in Templates

| Template | Background | Accent Color | Font | Use Case |
|----------|------------|--------------|------|----------|
| `tech_news` | Dark (#1a1a2e) | Cyan (#00d9ff) | Montserrat Bold | Tech updates, news |
| `data_story` | Light (#f8f9fa) | Blue (#3498db) | Open Sans Bold | Data viz, statistics |
| `explainer` | White (#FFFFFF) | Green (#00b894) | Roboto Medium | Educational, how-to |
| `listicle` | Black (#0d0d0d) | Red (#ff6b6b) | Bebas Neue | Countdowns, lists |

### Using Templates

Specify a template when generating videos:

```bash
brainrot generate --template tech_news
brainrot generate --template explainer --voice calm
```

## Template Structure

Templates are JSON files with the following structure:

```json
{
  "name": "my_template",
  "display_name": "My Template",
  "description": "A custom template description",
  "version": "1.0.0",
  "background_style": {
    "type": "solid",
    "color": "#1a1a2e",
    "secondary_color": "#16213e",
    "gradient_direction": 180,
    "opacity": 1.0
  },
  "caption_style": {
    "font": "Montserrat Bold",
    "size": 68,
    "color": "#FFFFFF",
    "outline_color": "#00d9ff",
    "outline_width": 3,
    "margin_v": 100,
    "alignment": 2,
    "bold": true,
    "italic": false
  },
  "transition": {
    "type": "fade",
    "duration": 0.3,
    "easing": "ease-in-out"
  },
  "colors": {
    "primary": "#00d9ff",
    "secondary": "#0f3460",
    "background": "#1a1a2e",
    "text": "#FFFFFF",
    "text_secondary": "#a0a0a0",
    "accent": "#00d9ff",
    "outline": "#00d9ff"
  },
  "fonts": {
    "primary": "Montserrat Bold",
    "secondary": "Montserrat",
    "primary_size": 68,
    "secondary_size": 42,
    "line_height": 1.3,
    "letter_spacing": 0.5
  },
  "animation_style": "kinetic",
  "caption_position": "bottom"
}
```

## Configuration Options

### Background Style

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `solid`, `gradient`, or `video` |
| `color` | string | Primary color (hex format) |
| `secondary_color` | string | Secondary color for gradients |
| `gradient_direction` | int | Gradient angle in degrees (0-360) |
| `opacity` | float | Background opacity (0.0-1.0) |

### Caption Style

| Field | Type | Description |
|-------|------|-------------|
| `font` | string | Font family name |
| `size` | int | Font size in pixels |
| `color` | string | Text color (hex format) |
| `outline_color` | string | Outline/stroke color |
| `outline_width` | int | Outline thickness in pixels |
| `margin_v` | int | Vertical margin from edge |
| `alignment` | int | Text alignment (1=left, 2=center, 3=right) |
| `bold` | boolean | Bold text |
| `italic` | boolean | Italic text |

### Color Palette

| Field | Description |
|-------|-------------|
| `primary` | Main accent color |
| `secondary` | Secondary/muted accent |
| `background` | Background color |
| `text` | Primary text color |
| `text_secondary` | Muted text color |
| `accent` | Highlight color |
| `outline` | Caption outline color |

### Typography

| Field | Type | Description |
|-------|------|-------------|
| `primary` | string | Main font family |
| `secondary` | string | Secondary font family |
| `primary_size` | int | Main font size |
| `secondary_size` | int | Secondary font size |
| `line_height` | float | Line height multiplier |
| `letter_spacing` | float | Letter spacing in pixels |

### Transition

| Field | Type | Options |
|-------|------|---------|
| `type` | string | `fade`, `slide`, `zoom`, `wipe`, `none` |
| `duration` | float | Duration in seconds |
| `easing` | string | `ease-in`, `ease-out`, `ease-in-out` |

### Animation Style

| Value | Description |
|-------|-------------|
| `static` | No animation, fixed captions |
| `kinetic` | Dynamic word-by-word appearance |
| `smooth` | Smooth fade transitions |

### Caption Position

| Value | Description |
|-------|-------------|
| `top` | Captions at top of screen |
| `center` | Captions in center |
| `bottom` | Captions at bottom (default) |

## Creating Custom Templates

### Step 1: Create the JSON File

Create a new JSON file in `brainrot/templates/`:

```bash
touch brainrot/templates/my_custom.json
```

### Step 2: Define Your Template

```json
{
  "name": "my_custom",
  "display_name": "My Custom Template",
  "description": "A vibrant template for lifestyle content",
  "version": "1.0.0",
  "background_style": {
    "type": "solid",
    "color": "#ff6b9d",
    "opacity": 1.0
  },
  "caption_style": {
    "font": "Poppins Bold",
    "size": 64,
    "color": "#FFFFFF",
    "outline_color": "#c44569",
    "outline_width": 4,
    "margin_v": 120,
    "alignment": 2,
    "bold": true
  },
  "transition": {
    "type": "slide",
    "duration": 0.4,
    "easing": "ease-out"
  },
  "colors": {
    "primary": "#ff6b9d",
    "secondary": "#c44569",
    "background": "#ff6b9d",
    "text": "#FFFFFF",
    "text_secondary": "#ffeaa7",
    "accent": "#ffeaa7",
    "outline": "#c44569"
  },
  "fonts": {
    "primary": "Poppins Bold",
    "secondary": "Poppins",
    "primary_size": 64,
    "secondary_size": 40,
    "line_height": 1.4,
    "letter_spacing": 0.3
  },
  "animation_style": "smooth",
  "caption_position": "bottom"
}
```

### Step 3: Test Your Template

```bash
brainrot generate --template my_custom
```

## Color Guidelines

### Contrast Ratios

Ensure readable captions by checking contrast:

| Background | Text Color | Ratio | Status |
|------------|------------|-------|--------|
| Dark (#1a1a2e) | White (#FFFFFF) | 14.5:1 | Good |
| Light (#f8f9fa) | Dark (#2d3436) | 12.8:1 | Good |
| White (#FFFFFF) | Black (#000000) | 21:1 | Excellent |

### Color Format

Colors use hex format: `#RRGGBB`

Example conversions:
- White: `#FFFFFF`
- Black: `#000000`
- Red: `#FF0000`
- Cyan: `#00FFFF`

## Font Recommendations

### Bold Fonts (Recommended for Captions)

| Font | Style | Best For |
|------|-------|----------|
| Montserrat Bold | Modern, geometric | Tech, news |
| Poppins Bold | Rounded, friendly | Lifestyle, casual |
| Bebas Neue | Tall, condensed | Listicles, countdowns |
| Roboto Medium | Clean, neutral | Educational |
| Open Sans Bold | Simple, readable | Data stories |

### Font Availability

Fonts must be installed on your system. Check available fonts:

```bash
# macOS
fc-list : family

# Linux
fc-list | cut -d: -f2 | sort -u
```

### Installing Fonts

**macOS:**
1. Download font files (.ttf or .otf)
2. Open Font Book
3. Drag fonts to install

**Linux:**
```bash
mkdir -p ~/.local/share/fonts
cp YourFont.ttf ~/.local/share/fonts/
fc-cache -fv
```

## Programmatic Usage

### Loading Templates in Python

```python
from brainrot.templates import TemplateRenderer, list_templates

# List available templates
templates = list_templates()
print(templates)  # ['data_story', 'explainer', 'listicle', 'tech_news']

# Load and apply a template
renderer = TemplateRenderer("tech_news")
style = renderer.get_caption_style()
print(style.font_family)  # Montserrat Bold
```

### Creating Videos with Templates

```python
from pathlib import Path
from brainrot.templates import TemplateRenderer
from brainrot.video import VideoBuilder

# Initialize
builder = VideoBuilder()
renderer = TemplateRenderer("explainer")

# Configure video
builder.add_background("#FFFFFF", duration=30.0)
renderer.apply_to_builder(builder, script, audio_path, duration)

# Render
video_path = builder.render("output.mp4")
```

## Best Practices

1. **Test on mobile**: Videos are 1080x1920 (vertical). Preview on phone.
2. **Keep captions short**: 3-5 words per line maximum.
3. **Use high contrast**: Ensure text is readable against background.
4. **Match mood to content**: Dark templates for serious content, bright for casual.
5. **Consistent branding**: Use similar colors across your content.

## Troubleshooting

### Font Not Found

If you see a default font instead of your chosen font:

1. Verify font is installed: `fc-list | grep "FontName"`
2. Use exact font family name from Font Book/fc-list
3. Restart any running processes after installing fonts

### Colors Look Wrong

ASS subtitle format uses `&HAABBGGRR` (alpha, blue, green, red). The template system converts hex automatically, but verify if colors appear inverted.

### Captions Cut Off

Adjust `margin_v` and font size:
- Increase `margin_v` for more padding
- Decrease `size` for smaller text
- Check `alignment` (2 = center, 1 = left, 3 = right)
