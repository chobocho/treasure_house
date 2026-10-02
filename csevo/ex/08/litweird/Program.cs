// 슬라이드 p8-v7-literals-weird — 제안서의 이상한 예와 _, C# 7.0
using System;

class App
{
    static void Main()
    {
        int weird = 1_2__3___4____5_____6______7_______8________9;
        double real = 1_000.111_1e-1_000;   // from the proposal
        int _1000 = 5;      // a leading _ makes an identifier
        int hex = 0x1b_a0_44_fe;

        Console.WriteLine(weird);
        Console.WriteLine(real);
        Console.WriteLine(_1000 + 1);
        Console.WriteLine(hex);

        int n;
        Console.WriteLine(int.TryParse("1_000", out n) + " " + n);
        Console.WriteLine(Convert.ToInt32("1010", 2));
    }
}
