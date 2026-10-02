// 슬라이드 p9-v8-ro-meta — readonly 멤버의 메타데이터, C# 8.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

struct Pt
{
    public int X;
    public readonly int Get() => X;
    public int Set(int v) => X = v;
    public readonly int Prop => X;
}

class App
{
    static void Show(MethodInfo m) =>
        Console.WriteLine("{0,-9} IsReadOnly={1}", m.Name,
            m.IsDefined(typeof(IsReadOnlyAttribute), false));

    static void Main()
    {
        Show(typeof(Pt).GetMethod("Get"));
        Show(typeof(Pt).GetMethod("Set"));
        Show(typeof(Pt).GetProperty("Prop").GetMethod);
        Console.WriteLine("struct itself: " + typeof(Pt)
            .IsDefined(typeof(IsReadOnlyAttribute), false));
    }
}
