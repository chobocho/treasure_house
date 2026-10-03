// 슬라이드 p12-v11-utf8-data — u8 이 낮춰지는 곳, C# 11.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

class App
{
    static void Main()
    {
        ReadOnlySpan<byte> hello = "hello"u8;
        ReadOnlySpan<byte> joined = "h"u8 + "el"u8 + "lo"u8;
        ref byte first = ref MemoryMarshal.GetReference(hello);
        byte after = Unsafe.Add(ref first, hello.Length);
        Console.WriteLine($"length {hello.Length}, after: {after}");
        Console.WriteLine(hello.SequenceEqual(joined));

        Type pid = typeof(App).Assembly.GetType(
            "<PrivateImplementationDetails>");
        const BindingFlags All = BindingFlags.Static
            | BindingFlags.NonPublic | BindingFlags.Public;
        foreach (FieldInfo f in pid.GetFields(All))
            Console.WriteLine("data field: " + f.FieldType.Name);
    }
}
