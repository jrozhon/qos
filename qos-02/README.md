# Exercise QoS_2

## Random variable:
 ``` It is an arbitrary quantity that can be repeatedly measured at different objects, at different locations, at different times, etc. These values can be further refined by methods of probability theory or mathematical statistics.```
 
For example, throwing a dice, waiting in line...

## History:
Abraham de Moivre was often challenged in the 18th century whether he would be able to shorten the long calculations of given mathematical problems of his time. An example of a probability calculation is given here - if we flip a coin 100 times, what is the probability that it will come up heads 40 times or more. The given problem could be calculated using the following formula:

$P(x) = \frac{N!}{x!(N-x)}\pi^{x}(1 - \pi)^{(N-x)}$, 

where x is the number of heads thrown (40), N is the number of throws (100), and $\pi$ is the probability that a head is thrown (0.5). That way, we would always have to calculate the probability that a head is rolled 40 times, then 41 times, etc., and add all those probabilities together. Previously, the possibility of computers and calculators did not exist, and that is why they turned to Moivre. He noted that if they increased the number of throws, the shape of the binomial distribution would approach a smooth curve. 

 ![Normal distribution](https://imgur.com/xHIXPNV.png) 

 Approximation of the binomial distribution by the normal distribution
 
 The distributions can be discrete and continuous according to NV - i.e. continuous NV = continuous distribution and vice versa. Continuous distributions are defined by formulas, probability density, or distribution function.


## Uniform distribution:
```The uniform distribution is one of the simplest distributions. This distribution has the same probability for all values of the random variable. This distribution has a continuous random variable X whose realizations fill an interval of finite length and have the same probability of occurrence.```

 ![Uniform distribution](https://imgur.com/oH6daj7.png) 
  
For example, these are all events that have the same possibility of frequency of occurrence (e.g. waiting time for a bus, for a product at an automatic line, etc.). 

## Exponential distribution:
```This distribution has a continuous random variable X, which represents the waiting time until the onset of a (Poisson) random event, or the length of the interval (in time or length) between such two events (e.g., the waiting time for an operator, the distance between two damaged locations on a road).``` 

```  The exponential distribution expresses the distribution of the length of the interval between randomly occurring events whose probability of occurrence has a Poisson distribution.``` 

It depends on the parameter $\lambda$, which is the inverse of the mean value of the waiting time until the occurrence of the monitored event.

 ![Exponential distribution](https://imgur.com/JqiSAHO.png) 

### Poisson process:
```The most used input flow model. We use the Poisson flow model always when customers (incoming calls, data packets, ...) come from a large set of mutually independent users.```

**Example:**

On an hourly on average, 15 customers come to the payphone. Each call takes an average of 3 minutes. Is it necessary to buy another payphone if we don't want customers to wait longer than 3 minutes? The arrival of customers follows a Poisson process, the time to make a call is random and follows an exponential distribution.


## Normal distribution:
```The normal distribution plays the largest role among continuous distributions in probability theory and statistics, and it governs (at least "approximately") more random variables (variables whose values are uniquely determined by the outcome of a random experiment). ```

As an example, we can mention the amount of random errors occurring in any activity (e.g. deviations in dimensions from a predetermined standard in the manufacture of components), as well as in most measurable characteristics of biological statistical units (in livestock, in experimental cell cultures, but also in humans, etc.). 

To be very specific, we find normal distributions for e.g. weight, IQ, height, etc.

 ![Normal distribution](https://imgur.com/xp3kOZz.png) 

## Basics of Queuing System:
```A Queuing System can be defined as a system consisting of one or more parallel lines (channels) for servicing incoming requests (customers).```

The basic elements of mass handling systems (Queuing System) are defined as:

**1. Requirements** (customers)

**2. Service lines** (service channels)
    
The Queuing System works in such a way that requests (customers) requiring service come to a device (one or more parallel lines of the service).
  Each Queuing System has a finite number of service lines - this number determines the maximum number of parallel (simultaneous) requests to be served - the so-called service capacity.
If there is a vacancy for service (a free service line), the request is accepted and service is started immediately.

#### Queuing System classification:
- it is necessary to describe the laws of the request origin and arrival in the system, the so-called input flow
- it is necessary to describe the number of service lines and to describe the flow of the service itself
- it is necessary to describe the process of serving customers in case they cannot be
not be served immediately (queuing mode)
- The most commonly used is the so-called Kendall classification of Queuing System
expresses clearly the type of Queuing System according to its basic characteristics

**A/B/n encoding (short version)**
- type of process describing the request arrival to the service (**A**)
- type of service time distribution (**B**)
- number of service lines (**n**)

#### Basic OS - M/M/1 type:
- The simplest case of the exponential model,
- one service channel (service facility),
- the intervals between request arrivals and servicing times have an exponential distribution, the queue size is not limited, the number of incoming requests is unlimited, all requests wait patiently in the queue for servicing even if the capacity of the servicing device is insufficient (FIFO queue).

In the notation, the M stands for Markovian; M/M/1 means that the system has a Poisson arrival process, an exponential service time distribution, and one server. 


