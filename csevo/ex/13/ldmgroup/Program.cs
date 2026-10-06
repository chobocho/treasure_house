// 슬라이드 p13-v12-ld-mgroup — 메서드 그룹의 기본값·params, C# 12
using System;

class Program
{
    static int AddWithDefault(int addTo = 2) => addTo + 1;
    static int Counter(params int[] xs) => xs.Length;

    static void Main()
    {
        var add1 = AddWithDefault;      // the proposal's example
        Console.WriteLine(add1() + " " + add1(5));
        var counter1 = Counter;
        Console.WriteLine(counter1(1, 2, 3) + " " + counter1());
        Console.WriteLine(add1.GetType().Name + " "
                          + counter1.GetType().Name);
    }
}
