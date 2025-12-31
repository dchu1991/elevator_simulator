"""
Pygame Visualization for Elevator Simulator
==========================================

A modern graphical visualization of the elevator system using pygame,
featuring real-time animations, interactive controls, and detailed status displays.
"""

import pygame
import time
from typing import Optional, Tuple
from dataclasses import dataclass

from src.core.simulation_engine import SimulationEngine
from src.core.elevator_simulator import ElevatorState, Direction


@dataclass
class Colors:
    """Color scheme for the pygame visualization"""

    BACKGROUND = (20, 20, 30)
    BUILDING = (60, 60, 80)
    FLOOR = (100, 100, 120)
    ELEVATOR_EMPTY = (80, 150, 80)
    ELEVATOR_OCCUPIED = (150, 150, 80)
    ELEVATOR_MOVING = (150, 80, 80)
    PERSON_WAITING = (200, 100, 100)
    PERSON_IN_ELEVATOR = (100, 200, 100)
    TEXT = (255, 255, 255)
    BUTTON_NORMAL = (70, 70, 90)
    BUTTON_HOVER = (90, 90, 110)
    BUTTON_ACTIVE = (110, 110, 130)
    SHAFT = (40, 40, 50)
    REQUEST_INDICATOR = (255, 255, 0)


class PygameVisualization:
    """Main pygame visualization class"""

    def __init__(
        self,
        simulation: SimulationEngine,
        width: int = 1200,
        height: int = 800,
    ):
        """Initialize pygame visualization"""
        self.simulation = simulation
        self.width = width
        self.height = height
        self.running = False

        # Initialize pygame
        pygame.init()
        pygame.font.init()

        # Create display
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Elevator Mall Simulator")

        # Fonts
        self.font_large = pygame.font.Font(None, 24)
        self.font_medium = pygame.font.Font(None, 18)
        self.font_small = pygame.font.Font(None, 14)

        # Layout configuration
        self.building_area = pygame.Rect(50, 50, 600, height - 100)
        self.control_area = pygame.Rect(670, 50, 500, height - 100)
        self.status_area = pygame.Rect(50, height - 80, width - 100, 60)

        # Animation state
        self.elevator_positions = {}  # Smooth positions for animation
        self.animation_speed = 0.1

        # Control state
        self.buttons = {}
        self.selected_elevator = 0

        # Clock for frame rate control
        self.clock = pygame.time.Clock()

        self._setup_buttons()

    def _setup_buttons(self):
        """Setup interactive buttons"""
        button_width = 120
        button_height = 30
        start_y = 100
        spacing = 40

        buttons_config = [
            ("Add Request", "add_request"),
            ("Pause/Resume", "toggle_pause"),
            ("Reset", "reset"),
            ("Statistics", "stats"),
            ("Exit", "exit"),
        ]

        for i, (text, action) in enumerate(buttons_config):
            button_rect = pygame.Rect(
                self.control_area.x + 20,
                start_y + i * spacing,
                button_width,
                button_height,
            )
            self.buttons[action] = {
                "rect": button_rect,
                "text": text,
                "pressed": False,
                "hover": False,
            }

    def start(self):
        """Start the pygame visualization"""
        self.running = True
        self.simulation.start_simulation()

        # Initialize elevator positions
        for elevator in self.simulation.building.elevators:
            self.elevator_positions[elevator.id] = float(elevator.current_floor)

        try:
            self._main_loop()
        finally:
            self._cleanup()

    def _main_loop(self):
        """Main pygame event and rendering loop"""
        while self.running:
            # Handle events
            self._handle_events()

            # Update animation positions
            self._update_animations()

            # Render everything
            self._render()

            # Control frame rate
            self.clock.tick(60)  # 60 FPS

    def _handle_events(self):
        """Handle pygame events"""
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self._handle_click(mouse_pos)

            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_hover(mouse_pos)

            elif event.type == pygame.KEYDOWN:
                self._handle_keypress(event.key)

    def _handle_click(self, mouse_pos: Tuple[int, int]):
        """Handle mouse clicks"""
        for action, button in self.buttons.items():
            if button["rect"].collidepoint(mouse_pos):
                self._execute_button_action(action)
                break

        # Check if clicked on elevator (for selection)
        elevator_clicked = self._get_elevator_at_position(mouse_pos)
        if elevator_clicked is not None:
            self.selected_elevator = elevator_clicked

    def _handle_mouse_hover(self, mouse_pos: Tuple[int, int]):
        """Handle mouse hover effects"""
        for button in self.buttons.values():
            button["hover"] = button["rect"].collidepoint(mouse_pos)

    def _handle_keypress(self, key):
        """Handle keyboard input"""
        if key in [pygame.K_ESCAPE, pygame.K_q]:
            self.running = False
        elif key == pygame.K_SPACE:
            self._execute_button_action("toggle_pause")
        elif key == pygame.K_r:
            self._execute_button_action("reset")
        elif key == pygame.K_a:
            self._execute_button_action("add_request")

    def _execute_button_action(self, action: str):
        """Execute button action"""
        if action == "add_request":
            self._show_add_request_dialog()
        elif action == "exit":
            self.running = False
        elif action == "stats":
            self._show_statistics()

    def _show_add_request_dialog(self):
        """Show dialog to add elevator request"""
        # For now, add a random request
        import random

        from_floor = random.randint(1, self.simulation.building.num_floors)
        to_floor = random.randint(1, self.simulation.building.num_floors)
        while to_floor == from_floor:
            to_floor = random.randint(1, self.simulation.building.num_floors)

        # Add person to simulation using the building's method
        from src.core.elevator_simulator import Person

        person = Person(
            id=random.randint(1000, 9999),
            current_floor=from_floor,
            destination_floor=to_floor,
            arrival_time=time.time(),
        )
        self.simulation.building.add_person_request(person)

    def _show_statistics(self):
        """Show current statistics"""
        stats = self.simulation.get_current_statistics()
        print(
            f"Statistics: {stats['total_people_completed']} completed, "
            f"avg wait: {stats.get('avg_journey_time', 0):.1f}s"
        )

    def _get_elevator_at_position(self, mouse_pos: Tuple[int, int]) -> Optional[int]:
        """Get elevator ID at mouse position"""
        # Calculate if mouse is over an elevator
        building_rect = self.building_area
        num_elevators = len(self.simulation.building.elevators)
        elevator_width = building_rect.width // (num_elevators + 1)

        for i, elevator in enumerate(self.simulation.building.elevators):
            elevator_x = (
                building_rect.x + (i + 1) * elevator_width - elevator_width // 4
            )
            elevator_rect = pygame.Rect(
                elevator_x, 0, elevator_width // 2, building_rect.height
            )

            if elevator_rect.collidepoint(mouse_pos):
                return elevator.id
        return None

    def _update_animations(self):
        """Update smooth animation positions"""
        for elevator in self.simulation.building.elevators:
            target_floor = float(elevator.current_floor)
            current_pos = self.elevator_positions.get(elevator.id, target_floor)

            # Smooth interpolation
            diff = target_floor - current_pos
            if abs(diff) > 0.01:
                self.elevator_positions[elevator.id] = (
                    current_pos + diff * self.animation_speed
                )
            else:
                self.elevator_positions[elevator.id] = target_floor

    def _render(self):
        """Render the entire scene"""
        # Clear screen
        self.screen.fill(Colors.BACKGROUND)

        # Render building
        self._render_building()

        # Render elevators
        self._render_elevators()

        # Render control panel
        self._render_controls()

        # Render status bar
        self._render_status()

        # Update display
        pygame.display.flip()

    def _render_building(self):
        """Render the building structure"""
        building_rect = self.building_area

        # Draw building outline
        pygame.draw.rect(self.screen, Colors.BUILDING, building_rect, 2)

        # Draw floors
        num_floors = self.simulation.building.num_floors
        floor_height = building_rect.height / num_floors

        for floor_num in range(num_floors):
            y = building_rect.bottom - floor_num * floor_height
            floor_rect = pygame.Rect(building_rect.x, y, building_rect.width, 2)
            pygame.draw.rect(self.screen, Colors.FLOOR, floor_rect)

            # Floor number
            floor_text = self.font_small.render(str(floor_num + 1), True, Colors.TEXT)
            self.screen.blit(floor_text, (building_rect.x - 25, y - 8))

            # Show waiting people
            self._render_waiting_people(floor_num + 1, y, floor_height)

    def _render_waiting_people(
        self, floor_number: int, y_position: float, floor_height: float
    ):
        """Render people waiting on a floor"""
        # Get waiting people - use .get() to avoid KeyError
        waiting_up = self.simulation.building.waiting_up.get(floor_number, [])
        waiting_down = self.simulation.building.waiting_down.get(floor_number, [])
        all_waiting = waiting_up + waiting_down

        # Filter out people who are already in elevators (safety check for race conditions)
        people_in_elevators = set()
        for elevator in self.simulation.building.elevators:
            people_in_elevators.update(id(p) for p in elevator.passengers)

        all_waiting = [p for p in all_waiting if id(p) not in people_in_elevators]

        if not all_waiting:
            return

        # Show waiting people as small circles
        waiting_count = len(all_waiting)
        people_per_row = 10
        circle_size = 3

        for i, person in enumerate(all_waiting[:30]):  # Limit display
            row = i // people_per_row
            col = i % people_per_row

            person_x = self.building_area.x + 10 + col * (circle_size * 2 + 1)
            person_y = y_position - floor_height + 5 + row * (circle_size * 2 + 1)

            pygame.draw.circle(
                self.screen,
                Colors.PERSON_WAITING,
                (int(person_x), int(person_y)),
                circle_size,
            )

        # Show count if too many people
        if waiting_count > 30:
            count_text = self.font_small.render(
                f"+{waiting_count - 30}", True, Colors.TEXT
            )
            self.screen.blit(
                count_text,
                (self.building_area.x + 250, y_position - floor_height + 5),
            )

    def _render_elevators(self):
        """Render all elevators"""
        building_rect = self.building_area
        num_elevators = len(self.simulation.building.elevators)
        num_floors = self.simulation.building.num_floors

        elevator_width = building_rect.width // (num_elevators + 1)
        floor_height = building_rect.height / num_floors

        for i, elevator in enumerate(self.simulation.building.elevators):
            # Calculate elevator position
            elevator_x = (
                building_rect.x + (i + 1) * elevator_width - elevator_width // 4
            )

            # Get smooth position
            smooth_floor = self.elevator_positions.get(
                elevator.id, elevator.current_floor
            )
            # Convert floor number (1-based) to 0-based for positioning calculation
            floor_position = smooth_floor - 1
            # Clamp floor position to valid range
            floor_position = max(0, min(floor_position, num_floors - 1))
            elevator_y = (
                building_rect.bottom - floor_position * floor_height - floor_height // 2
            )

            # Draw elevator shaft
            shaft_rect = pygame.Rect(
                elevator_x,
                building_rect.y,
                elevator_width // 2,
                building_rect.height,
            )
            pygame.draw.rect(self.screen, Colors.SHAFT, shaft_rect)

            # Choose elevator color based on state
            if elevator.state == ElevatorState.MOVING:
                color = Colors.ELEVATOR_MOVING
            elif elevator.passengers:
                color = Colors.ELEVATOR_OCCUPIED
            else:
                color = Colors.ELEVATOR_EMPTY

            # Draw elevator car
            elevator_rect = pygame.Rect(
                elevator_x + 2,
                elevator_y - floor_height // 4,
                elevator_width // 2 - 4,
                floor_height // 2,
            )
            pygame.draw.rect(self.screen, color, elevator_rect)

            # Highlight selected elevator
            if elevator.id == self.selected_elevator:
                pygame.draw.rect(
                    self.screen, Colors.REQUEST_INDICATOR, elevator_rect, 3
                )

            # Draw direction arrow
            self._render_elevator_direction(elevator, elevator_rect)

            # Draw passenger count
            passenger_count = len(elevator.passengers)
            if passenger_count > 0:
                count_text = self.font_small.render(
                    str(passenger_count), True, Colors.TEXT
                )
                text_rect = count_text.get_rect(center=elevator_rect.center)
                self.screen.blit(count_text, text_rect)

            # Draw elevator ID
            id_text = self.font_small.render(f"E{elevator.id}", True, Colors.TEXT)
            self.screen.blit(id_text, (elevator_x, building_rect.y - 20))

    def _render_elevator_direction(self, elevator, elevator_rect):
        """Render direction arrow for elevator"""
        if elevator.direction == Direction.UP:
            # Up arrow
            points = [
                (elevator_rect.centerx, elevator_rect.top + 5),
                (elevator_rect.centerx - 5, elevator_rect.top + 10),
                (elevator_rect.centerx + 5, elevator_rect.top + 10),
            ]
            pygame.draw.polygon(self.screen, Colors.REQUEST_INDICATOR, points)
        elif elevator.direction == Direction.DOWN:
            # Down arrow
            points = [
                (elevator_rect.centerx, elevator_rect.bottom - 5),
                (elevator_rect.centerx - 5, elevator_rect.bottom - 10),
                (elevator_rect.centerx + 5, elevator_rect.bottom - 10),
            ]
            pygame.draw.polygon(self.screen, Colors.REQUEST_INDICATOR, points)

    def _render_controls(self):
        """Render the control panel"""
        control_rect = self.control_area

        # Panel background
        pygame.draw.rect(self.screen, Colors.BUILDING, control_rect)
        pygame.draw.rect(self.screen, Colors.TEXT, control_rect, 2)

        # Title
        title_text = self.font_large.render("Controls", True, Colors.TEXT)
        self.screen.blit(title_text, (control_rect.x + 20, control_rect.y + 20))

        # Render buttons
        for action, button in self.buttons.items():
            # Button color based on state
            if button["pressed"]:
                color = Colors.BUTTON_ACTIVE
            elif button["hover"]:
                color = Colors.BUTTON_HOVER
            else:
                color = Colors.BUTTON_NORMAL

            # Draw button
            pygame.draw.rect(self.screen, color, button["rect"])
            pygame.draw.rect(self.screen, Colors.TEXT, button["rect"], 2)

            # Button text
            text_surface = self.font_medium.render(button["text"], True, Colors.TEXT)
            text_rect = text_surface.get_rect(center=button["rect"].center)
            self.screen.blit(text_surface, text_rect)

        # Show elevator details
        self._render_elevator_details()

    def _render_elevator_details(self):
        """Render detailed information about elevators"""
        start_y = 350
        line_height = 20

        details_title = self.font_medium.render("Elevator Details", True, Colors.TEXT)
        self.screen.blit(details_title, (self.control_area.x + 20, start_y))

        current_y = start_y + 30

        for elevator in self.simulation.building.elevators:
            try:
                # Basic info
                info_text = f"E{elevator.id}: Floor {elevator.current_floor} - {elevator.state.value}"
                if elevator.direction != Direction.IDLE:
                    info_text += f" ({elevator.direction.value})"

                text_surface = self.font_small.render(info_text, True, Colors.TEXT)
                self.screen.blit(text_surface, (self.control_area.x + 30, current_y))
                current_y += line_height

                # Passenger info
                if elevator.passengers:
                    passenger_info = f"  Passengers: {len(elevator.passengers)} -> "
                    try:
                        destinations = sorted(
                            {p.destination_floor for p in elevator.passengers}
                        )
                        passenger_info += str(destinations)
                    except AttributeError as e:
                        passenger_info += f"Error accessing passenger data: {e}"

                    text_surface = self.font_small.render(
                        passenger_info, True, Colors.PERSON_IN_ELEVATOR
                    )
                    self.screen.blit(
                        text_surface, (self.control_area.x + 30, current_y)
                    )
                    current_y += line_height

                # Requests
                requests = []
                if elevator.up_requests:
                    requests.append(f"Up: {sorted(elevator.up_requests)}")
                if elevator.down_requests:
                    requests.append(f"Down: {sorted(elevator.down_requests)}")
                if elevator.destination_floors:
                    requests.append(f"Dest: {sorted(elevator.destination_floors)}")

                if requests:
                    request_info = f"  Requests: {' | '.join(requests)}"
                    text_surface = self.font_small.render(
                        request_info, True, Colors.REQUEST_INDICATOR
                    )
                    self.screen.blit(
                        text_surface, (self.control_area.x + 30, current_y)
                    )
                    current_y += line_height

                current_y += 5  # Extra space between elevators
            except Exception as e:
                error_text = f"E{elevator.id}: Error - {str(e)}"
                text_surface = self.font_small.render(error_text, True, (255, 0, 0))
                self.screen.blit(text_surface, (self.control_area.x + 30, current_y))
                current_y += line_height

    def _render_status(self):
        """Render status bar at bottom"""
        status_rect = self.status_area

        # Background
        pygame.draw.rect(self.screen, Colors.BUILDING, status_rect)
        pygame.draw.rect(self.screen, Colors.TEXT, status_rect, 1)

        # Get current statistics
        stats = self.simulation.get_current_statistics()

        # Status text
        status_text = (
            f"Time: {stats.get('elapsed_time', 0):.1f}s | "
            f"Completed: {stats['total_people_completed']} | "
            f"Waiting: {stats['people_waiting']} | "
            f"Avg Wait: {stats.get('avg_journey_time', 0):.1f}s | "
            f"Throughput: {stats['throughput']:.1f}/hour"
        )

        text_surface = self.font_medium.render(status_text, True, Colors.TEXT)
        self.screen.blit(text_surface, (status_rect.x + 10, status_rect.y + 20))

        # FPS counter
        fps_text = f"FPS: {self.clock.get_fps():.0f}"
        fps_surface = self.font_small.render(fps_text, True, Colors.TEXT)
        self.screen.blit(fps_surface, (status_rect.right - 80, status_rect.y + 5))

    def _cleanup(self):
        """Clean up pygame resources"""
        self.simulation.stop_simulation()
        pygame.quit()


def run_pygame_simulation(
    num_floors: int = 15,
    num_elevators: int = 3,
    duration_minutes: int = 10,
    debug: bool = False,
):
    """Run the pygame visualization with context manager for clean resource handling"""
    print(
        f"Starting pygame visualization: {num_floors} floors, {num_elevators} elevators"
    )

    # Use context manager for automatic cleanup
    with SimulationEngine(
        num_floors, num_elevators, time_scale=0.2, debug=debug
    ) as simulation:
        # Create and start pygame visualization
        visualization = PygameVisualization(simulation)

        try:
            visualization.start()
        except KeyboardInterrupt:
            print("\nShutting down pygame visualization...")
        except Exception as e:
            print(f"Error in pygame visualization: {e}")
        finally:
            visualization._cleanup()


if __name__ == "__main__":
    run_pygame_simulation()
