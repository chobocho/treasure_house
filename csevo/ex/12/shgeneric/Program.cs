// 슬라이드 p12-v11-sh-generic — BCL 의 IShiftOperators, C# 11.0
using System;
using System.Linq;
using System.Numerics;

class App
{
    // Normalize: shift left until the top bit is set
    static T Norm<T>(T x) where T : IBinaryInteger<T> =>
        x << int.CreateChecked(T.LeadingZeroCount(x));

    static string Shift(Type t) => t.GetInterfaces()
        .Where(i => i.Name.StartsWith("IShiftOperators"))
        .Select(i => string.Join(",",
            i.GetGenericArguments().Select(a => a.Name)))
        .Single();

    static void Main()
    {
        Console.WriteLine(Norm((byte)0b1011) + " " + Norm(11u)
            + " " + Norm((ushort)1));
        foreach (Type t in new[] { typeof(int), typeof(long),
            typeof(Int128), typeof(BigInteger), typeof(nint) })
            Console.WriteLine(t.Name.PadRight(11) + Shift(t));
    }
}
