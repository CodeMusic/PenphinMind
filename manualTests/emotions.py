# === MAIN LOOP ===

# Simple header showing current phase
def draw_simple_header(draw):
    # Fill header background
    draw.rectangle((0, 0, WIDTH - 3, HEADER_HEIGHT - 1), fill=(10, 10, 20))
    
    # Draw phase name
    phase_name = current_phase.replace("_", " ").title()
    text_width = len(phase_name) * 5  # Approximate width
    text_x = (WIDTH - 3 - text_width) // 2
    
    # Only display if there's no current notification
    if not current_notification and not notification_queue:
        draw.text((max(0, text_x), 4), phase_name, fill=EMOTION_COLORS["white"])
    else:
        # Handle notification display
        if notification_timer <= 0 and notification_queue:
            # Get next notification
            current_notification = notification_queue.pop(0)
            notification_timer = 20  # Show for 1 second (20 ticks at 0.05s per tick)
            
        if current_notification:
            # Draw notification background with emotion color
            draw.rectangle((0, 0, WIDTH - 3, HEADER_HEIGHT - 1), 
                         fill=EMOTION_COLORS[current_notification])
            
            # Draw emotion word in contrasting color
            word = EMOTION_WORDS.get(current_notification, "UNLOCKED")
            text_width = len(word) * 6  # Approximate width
            text_x = (WIDTH - 3 - text_width) // 2
            
            # Use black text on bright colors
            text_color = EMOTION_COLORS["black"] if current_notification in ["yellow", "orange", "green"] else EMOTION_COLORS["white"]
            draw.text((text_x, 4), word, fill=text_color)
            
            # Update timer
            notification_timer -= 1
            if notification_timer <= 0:
                current_notification = None

tick = 0
current_phase = "white_start"  # Start with white base
phase_timer = PHASE_DURATIONS[current_phase] * 20  # Convert to ticks (20 per second)
growing_colors = {"white": {"pos": (CENTER_X, CENTER_Y), "size": 0, "target": (CENTER_X, CENTER_Y)}}
merging_colors = []
merge_progress = 0
merge_result = None
final_swirl_counter = 0

try:
    # Main animation loop
    while True:
        # Create image and drawing context for this frame
        img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Update animation cycle
        update_animation_cycle(tick)
        
        # Draw the header (simplified version that shows current phase)
        draw_simple_header(draw)
        
        # Draw the main area with animation
        draw_main_area(draw)
        
        # Draw the ambient effect at the bottom
        draw_ambient(draw, tick)
        
        # Draw the color status indicator
        draw_color_status(draw, img)
        
        # Update the display with the RGB matrix
        matrix.SetImage(img.rotate(ROTATE) if ROTATE else img)
        
        # Increment tick and add small delay
        tick += 1
        time.sleep(0.05)

except KeyboardInterrupt:
    # Clean up on exit
    matrix.Clear()
    print("🧠 Emotion automaton ended.") 