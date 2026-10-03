// 슬라이드 p12-v11-math-family — 형식마다 다른 인터페이스 묶음, C# 11.0
using System;
using System.Linq;
using System.Numerics;

class App
{
    static readonly Type[] Ifs =
    {
        typeof(INumberBase<>), typeof(INumber<>),
        typeof(IBinaryInteger<>),
        typeof(IFloatingPoint<>), typeof(IMinMaxValue<>),
        typeof(ISignedNumber<>), typeof(IUnsignedNumber<>),
    };

    static void Row(Type t)
    {
        var have = t.GetInterfaces().Where(i => i.IsGenericType)
            .Select(i => i.GetGenericTypeDefinition()).ToHashSet();
        Console.WriteLine(t.Name.PadRight(11) + string.Concat(Ifs
            .Select(i => (have.Contains(i) ? "o" : ".").PadLeft(4))));
    }

    static void Main()
    {
        Console.WriteLine("".PadRight(11)
            + "  NB   N  BI  FP  MM  SN  UN");
        foreach (Type t in new[] { typeof(int), typeof(uint),
            typeof(double), typeof(decimal), typeof(Half),
            typeof(BigInteger), typeof(Complex), typeof(char) })
            Row(t);
    }
}
