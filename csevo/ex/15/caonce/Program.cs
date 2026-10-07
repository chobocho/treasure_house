// 슬라이드 p15-v14-ca-once — 왼쪽은 한 번만, 읽기 전용은 안 된다, C# 14
using System;

struct Acc
{
    public int N;
    public void operator +=(int d) => N += d;
    public readonly void operator -=(int d) =>
        Console.WriteLine("readonly -= " + d);
}

class Program
{
    static Acc[] arr = new Acc[2];
    static readonly Acc Fixed = new Acc();

    static int Index()
    {
        Console.WriteLine("Index()");
        return 1;
    }

    static void Use(in Acc a)
    {
#if INPARAM
        a -= 2;                   // readonly operator, 'in' target
#endif
    }

    static void Main()
    {
        arr[Index()] += 5;
        arr[Index()] -= 7;
        Console.WriteLine(arr[1].N + " " + Fixed.N);
        Use(arr[1]);
#if READONLY
        Fixed += 1;
#endif
    }
}
