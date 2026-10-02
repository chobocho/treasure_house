// 슬라이드 p8-v7-pat-compat — 맞을 수 없는 패턴은 오류, C# 7.0
class App
{
    static void Main()
    {
        int? i = 1;
        string s = "x";
        System.Console.WriteLine(i is long l);  // int? never a long
        System.Console.WriteLine(s is int n);   // string never an int
        dynamic d = 1;
        System.Console.WriteLine(d is dynamic x);
    }
}
