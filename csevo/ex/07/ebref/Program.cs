// 슬라이드 p7-v6-eb-ref — ref 를 돌려주는 식 본문, C# 7.0
using System;

class Buffer
{
    int[] items = { 1, 2, 3 };

    public ref int First => ref items[0];
    public int Sum() => items[0] + items[1] + items[2];
}

class Program
{
    static void Main()
    {
        Buffer b = new Buffer();
        b.First = 10;              // writes items[0] via the getter
        ref int f = ref b.First;
        f++;
        Console.WriteLine(b.Sum());
    }
}
