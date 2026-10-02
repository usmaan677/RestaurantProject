import { useState } from "react";
import { services } from "../mockData";

// Services may or may not have an `id`, so fall back to `name` as the lookup key.
// Always coerced to a string because <select> values are strings.
// if two services share a name and have no id, their keys will collide.
const getServiceKey = (service) => String(service.id ?? service.name);

function AdminQueue() {
  // Which service the admin is currently viewing. Defaults to the first one,
  // or "" if there are no services at all.
  const [selectedServiceKey, setSelectedServiceKey] = useState(
    services[0] ? getServiceKey(services[0]) : "",
  );

  // All queues live in one object keyed by service key: { [serviceKey]: Person[] }.
  // The lazy initializer (function form of useState) runs only on the first render.
  const [queues, setQueues] = useState(() =>
    Object.fromEntries(
      services.map((service) => {
        const serviceKey = getServiceKey(service);
        const initialQueue = Array.isArray(service.queue) ? service.queue : [];

        return [
          serviceKey,
          // Normalize every queue entry into { id, name, ...rest } so the rest of the
          // component can rely on a consistent shape. The mock data can contain:
          //   - plain strings (just a name), or
          //   - objects with `name` or `customerName`, and maybe no `id`.
          initialQueue.map((person, index) =>
            typeof person === "string"
              ? { id: `${serviceKey}-${index}`, name: person }
              : {
                  ...person,
                  // `id` is used as the React key and for removal, so it must be unique per queue.
                  id: person.id ?? `${serviceKey}-${index}`,
                  name:
                    person.name ??
                    person.customerName ??
                    `Customer ${index + 1}`,
                },
          ),
        ];
      }),
    ),
  );

  // Status message shown after an action (remove / serve). Cleared on service change.
  const [notice, setNotice] = useState("");

  // Derived values: computed on each render, not stored in state.
  const selectedService = services.find(
    (service) => getServiceKey(service) === selectedServiceKey,
  );
  const queue = queues[selectedServiceKey] ?? [];

  // Single entry point for every queue change (move, remove, serve).
  // It updates both React state and the shared mock data.
  function saveQueue(nextQueue) {
    if (selectedService) {
      // Update the mock data so other parts of the app can read the changes.
      selectedService.queue = nextQueue;
    }

    // Functional update so we never overwrite other services' queues with stale data.
    setQueues((current) => ({
      ...current,
      [selectedServiceKey]: nextQueue,
    }));
  }

  // Swap a person with their neighbor. `direction` is -1 (up) or +1 (down).
  function movePerson(index, direction) {
    const newIndex = index + direction;
    // Guard against moving past either end (buttons are also disabled in the UI).
    if (newIndex < 0 || newIndex >= queue.length) return;


    const updatedQueue = [...queue];
    // Destructuring swap of the two entries.
    [updatedQueue[index], updatedQueue[newIndex]] = [
      updatedQueue[newIndex],
      updatedQueue[index],
    ];

    saveQueue(updatedQueue);
  }

  // Remove by `id` rather than index so the right person is removed even if the list changes.
  function removePerson(person) {
    saveQueue(queue.filter((item) => item.id !== person.id));
    setNotice(`${person.name} was removed from the queue.`);
  }

  // The queue is first-in-first-out: serving takes the person at position 0.
  function serveNext() {
    if (queue.length === 0) return;

    const nextPerson = queue[0];
    saveQueue(queue.slice(1)); // slice returns a new array without the first item
    setNotice(`${nextPerson.name} is being served.`);
  }

  return (
    <main className="mx-auto max-w-2xl p-6">
      <h1 className="text-3xl font-bold text-slate-800">Manage Queues</h1>
      <p className="mt-2 text-slate-600">
        View and manage the queue for each service.
      </p>

      {/* Empty state: nothing to select, so skip the whole controls section. */}
      {services.length === 0 ? (
        <p className="mt-6 text-slate-600">No services are available.</p>
      ) : (
        <>
          {/* htmlFor/id pairing keeps the select accessible to screen readers. */}
          <label
            htmlFor="service"
            className="mt-6 block text-sm font-medium text-slate-700"
          >
            Service
          </label>

          <select
            id="service"
            value={selectedServiceKey}
            onChange={(event) => {
              setSelectedServiceKey(event.target.value);
              // Clear the notice so a message about one service
              // doesn't appear under a different one.
              setNotice("");
            }}
            className="mt-2 w-full rounded-md border border-slate-300 bg-white px-3 py-2"
          >
            {services.map((service) => (
              <option
                key={getServiceKey(service)}
                value={getServiceKey(service)}
              >
                {service.name}
              </option>
            ))}
          </select>

          <section className="mt-6 rounded-lg border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between gap-4">
              <h2 className="text-xl font-semibold text-slate-800">
                {selectedService?.name} queue
              </h2>

              {/* Disabled when empty so the admin can't serve nobody. */}
              <button
                type="button"
                onClick={serveNext}
                disabled={queue.length === 0}
                className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                Serve next
              </button>
            </div>

            {/* role="status" makes screen readers announce the message when it appears. */}
            {notice && (
              <p className="mt-3 text-sm text-green-700" role="status">
                {notice}
              </p>
            )}

            {queue.length === 0 ? (
              <p className="mt-6 text-slate-500">This queue is empty.</p>
            ) : (
              // <ol> because order matters in a queue.
              <ol className="mt-4 divide-y divide-slate-200">
                {queue.map((person, index) => (
                  // Use the stable person.id as the key, not the index,
                  // so React tracks rows correctly when they are reordered.
                  <li
                    key={person.id}
                    className="flex items-center justify-between gap-4 py-3"
                  >
                    <div>
                      <span className="mr-3 text-sm text-slate-500">
                        {index + 1}.
                      </span>
                      <span className="font-medium text-slate-800">
                        {person.name}
                      </span>
                    </div>

                    <div className="flex shrink-0 gap-2">
                      {/* aria-labels include the person's name so each button is
                          distinguishable to screen readers. The first person can't
                          move up and the last can't move down. */}
                      <button
                        type="button"
                        onClick={() => movePerson(index, -1)}
                        disabled={index === 0}
                        aria-label={`Move ${person.name} up`}
                        className="rounded border border-slate-300 px-3 py-1 text-sm disabled:opacity-40"
                      >
                        Up
                      </button>

                      <button
                        type="button"
                        onClick={() => movePerson(index, 1)}
                        disabled={index === queue.length - 1}
                        aria-label={`Move ${person.name} down`}
                        className="rounded border border-slate-300 px-3 py-1 text-sm disabled:opacity-40"
                      >
                        Down
                      </button>

                      {/* Removal is immediate with no confirmation step. I'll consider adding
                          one if accidental clicks become a problem. */}
                      <button
                        type="button"
                        onClick={() => removePerson(person)}
                        className="rounded border border-red-300 px-3 py-1 text-sm text-red-700 hover:bg-red-50"
                      >
                        Remove
                      </button>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </>
      )}
    </main>
  );
}

export default AdminQueue;
