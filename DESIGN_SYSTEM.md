# MIT Mysore Timetable System - Design System

## 🎨 Color Palette

### Primary Colors
- **Blue Primary**: `#3b82f6` - Main actions, primary buttons
- **Blue Dark**: `#2563eb` - Hover states, emphasis
- **Blue Darker**: `#1e40af` - Headers, titles

### Functional Colors
- **Success Green**: `#22c55e` - Save, confirm actions
- **Success Dark**: `#16a34a` - Hover state
- **Danger Red**: `#ef4444` - Delete, cancel actions
- **Danger Dark**: `#dc2626` - Hover state
- **Warning Orange**: `#f97316` - Alerts, warnings
- **Info Purple**: `#a855f7` - Information, special features

### Background Colors
- **Light Blue**: `#f0f9ff` - Page backgrounds (start)
- **Sky Blue**: `#e0f2fe` - Page backgrounds (end)
- **Pale Blue**: `#bae6fd` - Accent backgrounds
- **White**: `#ffffff` - Cards, containers
- **Gray Light**: `#f8fafc` - Input backgrounds
- **Gray Border**: `#e0f2fe` - Borders, dividers

### Text Colors
- **Dark**: `#1e293b` - Primary text
- **Blue**: `#1e40af` - Headings, links
- **Gray**: `#64748b` - Secondary text

## 📐 Spacing System

- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 20px
- **2xl**: 24px
- **3xl**: 32px

## 🔤 Typography

### Font Family
- Primary: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif

### Font Sizes
- **Small**: 12px - Labels, captions
- **Base**: 14px - Body text, inputs
- **Medium**: 16px - Buttons, important text
- **Large**: 20px - Subheadings
- **XLarge**: 28px - Page titles

### Font Weights
- **Normal**: 400
- **Medium**: 500
- **Semibold**: 600
- **Bold**: 700

## 🎭 Components

### Buttons
```css
Primary Button:
- Background: #3b82f6
- Hover: #2563eb
- Padding: 10-14px
- Border-radius: 8px
- Transition: 0.3s ease

Success Button:
- Background: #22c55e
- Hover: #16a34a

Danger Button:
- Background: #ef4444
- Hover: #dc2626
```

### Input Fields
```css
- Background: #f8fafc
- Border: 2px solid #e0f2fe
- Border-radius: 8px
- Padding: 8-12px
- Focus: border #3b82f6, shadow rgba(59, 130, 246, 0.1)
```

### Cards
```css
- Background: white
- Border: 1px solid #e0f2fe
- Border-radius: 8-12px
- Shadow: 0 2px 8px rgba(30, 64, 175, 0.08)
- Hover: translateY(-3px), enhanced shadow
```

### Tables
```css
Row Hover:
- Background: #f0f9ff
- Transform: translateX(2px)
- Transition: 0.2s ease
```

## ✨ Animations

### Transitions
- **Fast**: 0.2s ease - Hover effects, small changes
- **Normal**: 0.3s ease - Standard interactions
- **Slow**: 0.5s ease - Page loads, major changes

### Keyframes
```css
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes slideDown {
  from { transform: translateY(-100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
```

## 🎯 Hover Effects

### Buttons
- Transform: translateY(-2px)
- Enhanced shadow
- Darker background color

### Cards
- Transform: translateY(-3px to -5px)
- Enhanced shadow
- Border color change

### Table Rows
- Background color change
- Slight horizontal shift

## 📱 Responsive Breakpoints

- **Mobile**: < 768px
- **Tablet**: 768px - 1200px
- **Desktop**: > 1200px

## 🔧 Usage Guidelines

### When to Use Each Color

**Blue (#3b82f6)**
- Primary actions (Add, Next, Generate)
- Navigation elements
- Links and interactive elements

**Green (#22c55e)**
- Save operations
- Success confirmations
- Positive actions

**Red (#ef4444)**
- Delete operations
- Cancel actions
- Error states

**Orange (#f97316)**
- Warning messages
- Edit operations
- Secondary actions

**Purple (#a855f7)**
- Special features
- Information displays
- Tertiary actions

## 📋 Component Examples

### Page Structure
1. Header (Blue gradient)
2. Main content (White background)
3. Sidebar (White with border)
4. Footer (if needed)

### Form Layout
1. Label (Bold, dark text)
2. Input (Light background, blue border on focus)
3. Button (Color-coded by action)
4. Error message (Red text)

### Table Layout
1. Header (Light blue background)
2. Rows (White, hover effect)
3. Actions (Color-coded buttons)

## ✅ Accessibility

- Minimum contrast ratio: 4.5:1
- Focus states clearly visible
- Keyboard navigation supported
- Touch targets minimum 44x44px
- Alt text for images
- ARIA labels where needed

## 🚀 Performance

- CSS transitions instead of JavaScript animations
- Minimal shadow usage
- Optimized gradient animations
- Lazy loading for images
- Debounced input handlers
