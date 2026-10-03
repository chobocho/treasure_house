// 슬라이드 p12-v11-sa-runtime — 런타임이 보는 static abstract, C# 11.0
using System;
using System.Numerics;
using System.Reflection;
using System.Runtime.CompilerServices;

interface IZero<T> where T : IZero<T>
{
    static abstract T Zero { get; }
}

struct Cm : IZero<Cm> { public static Cm Zero => new Cm(); }

class App
{
    static void Main()
    {
        Console.WriteLine(RuntimeFeature.IsSupported(
            nameof(RuntimeFeature.VirtualStaticsInInterfaces)));

        MethodInfo get =
            typeof(IZero<Cm>).GetProperty("Zero").GetMethod;
        Console.WriteLine(get.Name + " static=" + get.IsStatic
            + " abstract=" + get.IsAbstract
            + " virtual=" + get.IsVirtual);

        // Interface map: which method of Cm fills the slot
        InterfaceMapping map =
            typeof(Cm).GetInterfaceMap(typeof(IZero<Cm>));
        for (int i = 0; i < map.InterfaceMethods.Length; i++)
            Console.WriteLine(map.InterfaceMethods[i].Name + " -> "
                + map.TargetMethods[i].DeclaringType.Name + "."
                + map.TargetMethods[i].Name.Replace("System.", ""));

        map = typeof(int).GetInterfaceMap(
            typeof(IAdditionOperators<int, int, int>));
        for (int i = 0; i < map.InterfaceMethods.Length; i++)
            Console.WriteLine(map.InterfaceMethods[i].Name + " -> "
                + map.TargetMethods[i].Name.Replace("System.", ""));
    }
}
