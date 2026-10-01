// 슬라이드 p2-v1-sizeof — 사용자 구조체의 sizeof 는 unsafe, C# 1.0
using System;

struct Pair { public int A; public Pair(int a) { A = a; } }

class App
{
    static void Main()
    {
        Console.WriteLine(sizeof(Pair));
        Console.WriteLine(sizeof(IntPtr));
    }
}
