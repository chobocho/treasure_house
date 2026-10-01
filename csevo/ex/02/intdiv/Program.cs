// 슬라이드 p2-v1-intdiv — 정수 나눗셈과 나머지의 부호, C# 1.0
using System;

class App
{
    static void Main()
    {
        Console.WriteLine(" 7 /  2 = " + (7 / 2));
        Console.WriteLine("-7 /  2 = " + (-7 / 2));     // toward zero
        Console.WriteLine("-7 %  2 = " + (-7 % 2));     // sign of left
        Console.WriteLine(" 7 % -2 = " + (7 % -2));
        Console.WriteLine("-7.5 % 2 = " + (-7.5 % 2));  // double too
        Console.WriteLine("(int)-2.7 = " + (int)-2.7);  // truncates
        Console.WriteLine("7 / 2 * 2.0 = " + (7 / 2 * 2.0));

        int min = int.MinValue, minus1 = -1;
        Console.WriteLine("min / -1 = " + unchecked(min / minus1));
    }
}
