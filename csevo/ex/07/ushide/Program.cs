// 슬라이드 p7-v6-us-hide — 내 멤버가 가져온 오버로드를 가린다, C# 6.0
using static System.Console;

class Program
{
    static void WriteLine(int n)
    {
        Write("my WriteLine: ");
        System.Console.WriteLine(n);
    }

    static void Main()
    {
        WriteLine(42);                 // Program.WriteLine(int)
        Write("imported Write\n");     // no Write in Program
#if BAD
        WriteLine("text");             // Console.WriteLine(string)?
#endif
    }
}
