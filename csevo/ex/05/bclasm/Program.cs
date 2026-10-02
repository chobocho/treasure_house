// 슬라이드 p5-v4-runtime-bcl — 그 밖의 형식들의 자리, C# 4.0
using System;
using System.Collections.Concurrent;
using System.Numerics;
using System.Threading;
using System.Threading.Tasks;

class Program
{
    static void Main()
    {
        Type[] types = {
            typeof(Task), typeof(Task<>), typeof(Parallel),
            typeof(CancellationToken), typeof(ConcurrentDictionary<,>),
            typeof(Lazy<>), typeof(Tuple), typeof(Tuple<,>),
            typeof(BigInteger), typeof(Complex),
        };
        foreach (Type t in types)
        {
            Console.WriteLine("{0,-46} {1}", t.FullName,
                              t.Assembly.GetName().Name);
        }
        Tuple<int, string> pair = Tuple.Create(4, "C#");
        Lazy<BigInteger> big = new Lazy<BigInteger>(
            delegate { return BigInteger.Pow(2, 100); });
        Console.WriteLine(pair.Item2 + " " + pair.Item1);
        Console.WriteLine(big.IsValueCreated + " " + big.Value);
    }
}
