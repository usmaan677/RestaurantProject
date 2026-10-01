// Mock data for the User screens. No backend yet, so everything here is static.

export const services = [
  {
    id: 1,
    name: 'Dine In',
    description: 'Sit down and enjoy your meal at the restaurant.',
    waitTime: 20,
    position: 3,
    status: 'Waiting',
  },
  {
    id: 2,
    name: 'Take Out',
    description: 'Pick up your order at the front counter.',
    waitTime: 10,
    position: 1,
    status: 'Almost Ready',
  },
  {
    id: 3,
    name: 'DoorDash',
    description: 'Have your order delivered to your door.',
    waitTime: 35,
    position: 6,
    status: 'Waiting',
  },
]

export const notifications = [
  { id: 1, message: 'Your Dine In queue position moved up to #3.', time: '2 mins ago' },
  { id: 2, message: 'Take Out orders are almost ready.', time: '10 mins ago' },
  { id: 3, message: 'Welcome to QueueSmart!', time: '1 hour ago' },
]

export const history = [
  { id: 1, service: 'Dine In', date: '2026-09-20', outcome: 'Served' },
  { id: 2, service: 'Take Out', date: '2026-09-18', outcome: 'Served' },
  { id: 3, service: 'DoorDash', date: '2026-09-15', outcome: 'Cancelled' },
]
