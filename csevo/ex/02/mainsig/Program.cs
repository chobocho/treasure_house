// 슬라이드 p2-v1-main — Main 의 네 가지 꼴과 종료 코드, C# 1.0
using System;

class Quiet
{
    static void Main() { }                   // 1. void, no args
}

class Echo
{
    static void Main(string[] args)          // 2. void, args
    {
        Console.WriteLine("echo: " + String.Join(" ", args));
    }
}

class Count
{
    static int Main()                        // 3. int, no args
    {
        return 0;
    }
}

class Check
{
    static int Main(string[] args)           // 4. int, args
    {
        Console.WriteLine("args: " + args.Length);
        Environment.ExitCode = 9;            // ignored: return wins
        return args.Length == 2 ? 0 : 2;
    }
}
