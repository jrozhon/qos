# Exercise 02 – Random variables, the Poisson process, and queueing systems

This exercise introduces the probabilistic tools used to describe network traffic. It reviews random variables and the uniform, exponential, and normal distributions, defines the Poisson process as the standard model of packet arrivals, and presents the M/M/1 queue together with Little's law. In the practical part, students generate random samples, build a discrete-event simulation of packet sources, a switch, and sinks in SimPy, and compare the measured delay and occupancy of a simulated M/M/1 system with the analytical formulas.

## Learning objectives

- Distinguish discrete and continuous random variables and read a probability mass or density function.
- Generate samples from the uniform, exponential, and normal distributions and interpret their histograms.
- Explain why the Poisson process models aggregated traffic and how it relates to exponential inter-arrival times.
- Read Kendall notation and state the assumptions of the M/M/1 model.
- Compute offered traffic, utilization, mean occupancy, and mean delay of an M/M/1 system and verify them by simulation.

## Theory

### Random variables

A *random variable* assigns a number to the outcome of a random experiment. It is *discrete* when it takes finitely or countably many values (the number of packets arriving in one second) and *continuous* when it takes any value in an interval (the time between two arrivals).

The behavior of a random variable $X$ is described by its *probability distribution*: a probability mass function (PMF) $P(X = k)$ for discrete variables, or a probability density function (PDF) $f(x)$ for continuous ones, where the probability of $X$ falling into an interval is the area under $f$ over that interval. Two numbers summarize a distribution:

- the *expectation* (mean) $E[X]$, the value around which outcomes are centered, and
- the *variance* $\operatorname{Var}[X] = E\big[(X - E[X])^2\big]$, the spread of outcomes around the mean; its square root is the standard deviation $\sigma$.

### Uniform distribution

The continuous uniform distribution on the interval $[a, b]$ assigns equal density to every value in the interval:

$$
f(x) = \frac{1}{b - a}, \qquad a \leq x \leq b
$$

where $a$ and $b$ are the interval bounds; the mean is $(a + b)/2$. Pseudo-random generators produce uniform samples on $[0, 1)$, from which samples of every other distribution are derived.

![Uniform distribution](fig/uniform.png)

### Exponential distribution

The exponential distribution describes the waiting time until the next event of a Poisson process, or equivalently the interval between two consecutive events:

$$
f(x) = \lambda e^{-\lambda x}, \qquad x \geq 0
$$

where $\lambda$ is the event rate [s⁻¹] and $1/\lambda$ the mean waiting time [s]. The distribution is *memoryless*: the time still to wait does not depend on how long one has already waited. This property is what makes the queueing models below tractable.

![Exponential distribution](fig/exponential.png)

### Normal distribution

The normal distribution, introduced in [Exercise 01](../qos-01/README.md#gaussian-noise), approximates any quantity that results from the sum of many small independent effects: measurement errors, dimensions of manufactured parts, or the noise on a channel. It is fully described by its mean $\mu$ and standard deviation $\sigma$. In this exercise it serves as a contrasting model of inter-arrival times that is *not* memoryless.

### Poisson process

The Poisson process is the standard model of an *input flow*: the arrival of calls, packets, or requests originating from a large population of mutually independent users. It is characterized by a single parameter, the arrival rate $\lambda$, and has two equivalent descriptions. First, the number of arrivals $N$ in an interval of length $t$ has the Poisson distribution

$$
P(N = k) = \frac{(\lambda t)^k}{k!} \, e^{-\lambda t}, \qquad k = 0, 1, 2, \dots
$$

where $\lambda$ is the arrival rate [s⁻¹] and $t$ the interval length [s]; the mean number of arrivals is $\lambda t$. Second, the intervals between consecutive arrivals are independent and exponentially distributed with rate $\lambda$.

The second description is the one used in simulation: a source that draws each inter-arrival time from an exponential distribution generates a Poisson process.

### Queueing systems

A *queueing system* serves incoming *requests* (customers, calls, packets) using one or more *service channels* (servers, lines). Its capacity is the number of requests that can be served simultaneously. A request that finds a free channel is served immediately; otherwise it either waits in a *queue* (a router buffer) or is rejected (a PBX without call waiting). A system is characterized by

- the input flow – how requests arrive,
- the service – the number of channels and the distribution of service times, and
- the queueing discipline – how waiting requests are managed (queue length, service order).

*Kendall notation* $A/B/n$ summarizes these: $A$ is the arrival process, $B$ the service-time distribution, and $n$ the number of channels. The symbol M (*Markovian*) denotes a Poisson process for $A$ and an exponential distribution for $B$; D denotes deterministic times and G a general distribution.

### The M/M/1 system

M/M/1 is the simplest queueing model: Poisson arrivals with rate $\lambda$, exponentially distributed service times with rate $\mu$ (mean service time $S = 1/\mu$), one channel, an unbounded queue, and first-in-first-out service. A switch port with a Poisson packet flow, exponentially distributed packet sizes, and a large buffer is an M/M/1 system.

The *offered traffic* (traffic intensity) is

$$
A = \lambda S = \frac{\lambda}{\mu}
$$

where $A$ is the offered traffic [erl], $\lambda$ the arrival rate [s⁻¹], $S$ the mean service time [s], and $\mu$ the service rate [s⁻¹]. For a single channel the *utilization* $\rho$, the fraction of time the server is busy, equals the offered traffic:

$$
\rho = \frac{\lambda}{\mu} = A
$$

The system is stable only for $\rho < 1$; otherwise the queue grows without bound.

> [!IMPORTANT]
> With $k$ channels (M/M/k) the utilization is $\rho = A/k$; the remaining formulas of this section hold for M/M/1 only.

For a stable M/M/1 system the mean number of requests in the system $L$ and in the queue $L_q$ are

$$
L = \frac{\rho}{1 - \rho}, \qquad L_q = L - \rho = \frac{\rho^2}{1 - \rho}
$$

and the mean time a request spends in the system $W$ and in the queue $W_q$ are

$$
W = \frac{1}{\mu - \lambda}, \qquad W_q = W - \frac{1}{\mu} = \frac{\rho}{\mu - \lambda}
$$

where $L$ and $L_q$ are dimensionless [–] and $W$ and $W_q$ are times [s]. All four quantities grow without bound as $\rho \to 1$, which is why links are operated well below full utilization.

### Little's law

Little's law relates occupancy and delay for *any* stable queueing system, regardless of the arrival and service distributions:

$$
L = \lambda W, \qquad L_q = \lambda W_q
$$

where $L$ is the mean number of requests in the system [–], $\lambda$ the arrival rate [s⁻¹], and $W$ the mean time in the system [s]; the second form applies to the queue alone. The law allows one of the three quantities to be obtained from measurements of the other two; in the simulation, the mean occupancy reported by a network tap and the mean delay reported by a sink should satisfy it.

## Exercise

### Preparation

Create the environment and start JupyterLab as described in the [root README](../README.md), then open `qos_02/exercise_02.ipynb`.

```bash
cd qos-02
uv sync
uv run jupyter lab --ip 0.0.0.0
```

The simulation components live in `lib/core.py` and are built on [SimPy](https://simpy.readthedocs.io/): `PacketSource` generates packets with a given inter-arrival time and size, `Switch` owns a set of `SwitchPort` objects, each a FIFO buffer of limited capacity draining at a fixed bit rate, `PacketSink` records the delay of every packet it receives, `NetworkTap` samples the occupancy of a port, and `PacketFork` splits a flow between destinations with given probabilities. Components are wired by assigning their `destination` attributes. Inter-arrival times and sizes may be constants or zero-argument callables; `functools.partial` applied to a NumPy random generator supplies the latter. Time is measured in simulation time units (STU).

### Step 1 – Generate random samples

Draw 10 000 samples from the uniform, exponential, and normal distributions with `numpy.random.Generator` and plot their histograms. Compare the sample minimum, mean, and maximum with the parameters of each distribution.

### Step 2 – Source and sink

Run the simplest simulation: one `PacketSource` sending directly to a `PacketSink`. Then extend it to two sources with different sizes and inter-arrival times, and replace the constants by distributions using `partial`.

### Step 3 – Source, switch, and sink

Insert a `Switch` between source and sink. The port has a buffer of 100 B and a transmission rate of 1000 bit/s; packets arrive with normally distributed intervals and exponentially distributed sizes. From the sink output, determine how long the packets spent in the system and whether any were dropped.

### Step 4 – Network tap

Attach a `NetworkTap` to the switch port used in Step 3 and inspect the packet and byte counts it records over time.

### Step 5 – M/M/1 system

Simulate the M/M/1 configuration in the notebook: exponential inter-arrival times with mean 2 STU, exponential packet sizes with mean 100 B, one port at 1000 bit/s with a 10 000 B buffer, for 8000 STU. Compute $\lambda$, $\mu$, and $\rho$ from these parameters, evaluate $L$, $W$, and $W_q$ analytically, and compare them with the average occupancy and average wait shown on the dashboard.

### Step 6 – A network of queues

Run the final simulation, in which three sources, two forks, and four switch ports form a small network. Identify the offered traffic on each port and explain the differences in the delays observed at the two sinks.

## Questions

1. Fifteen customers per hour arrive at a payphone according to a Poisson process, and a call lasts on average 3 minutes with an exponential distribution. Is a second payphone needed if the mean waiting time is not to exceed 3 minutes?
2. In Step 5, what are $\lambda$, $\mu$, and $\rho$, and which formula should the measured average wait match: $W$ or $W_q$?
3. What does Little's law predict for the mean occupancy in Step 5, and does the network tap confirm it?
4. Why does the mean delay of an M/M/1 system increase sharply as $\rho$ approaches 1, even though the server is still not saturated?
5. Which of the three distributions in Step 1 is memoryless, and why does that matter for the choice of a traffic model?

## References

1. L. Kleinrock, *Queueing Systems, Volume I: Theory*. Wiley, 1975.
2. D. Gross, J. F. Shortle, J. M. Thompson, and C. M. Harris, *Fundamentals of Queueing Theory*, 4th ed. Wiley, 2008.
3. J. D. C. Little, "A Proof for the Queuing Formula: L = λW," *Operations Research*, vol. 9, no. 3, pp. 383–387, 1961.
4. G. Bernstein, "Discrete Event Simulation in Python," Grotto Networking, https://www.grotto-networking.com/DiscreteEventPython.html — origin of the simulation components used in this exercise.
5. SimPy documentation, https://simpy.readthedocs.io/.
