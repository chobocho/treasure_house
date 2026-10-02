// 슬라이드 p8-v7_2-refreadonly — ref readonly 반환과 지역 변수, C# 7.2
using System;

struct Big
{
    public long A;
    public Big(long a) { A = a; }
}

class Store
{
    private readonly Big[] items = { new Big(1), new Big(2) };

    // a reference out, but no writes through it
    public ref readonly Big At(int i) => ref items[i];

    public void Set(int i, long a) { items[i].A = a; }
}

class App
{
    static void Main()
    {
        var s = new Store();
        ref readonly Big r = ref s.At(1);   // an alias, no copy
        Big copy = s.At(1);                 // the caller may copy
        s.Set(1, 99);
        Console.WriteLine("r.A    = " + r.A);
        Console.WriteLine("copy.A = " + copy.A);
        ref readonly var v = ref s.At(0);   // var works too
        Console.WriteLine("v.A    = " + v.A);
    }
}
