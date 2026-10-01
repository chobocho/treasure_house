// 슬라이드 p2-v1-line — #line 이 바꾸는 줄 번호, C# 1.0
using System;

class App
{
    static void Main()
    {
        int zero = 0;
        try
        {
#line 500 "Template.tt"
            Console.WriteLine(1 / zero);
#line default
        }
        catch (DivideByZeroException e)
        {
            Console.WriteLine(e.StackTrace.Trim());
        }
        string unused;
#line 900 "Template.tt"
        int y;
    }
}
