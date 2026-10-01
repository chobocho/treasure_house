// 슬라이드 p2-v1-catchorder — 넓은 catch 가 앞에 오면, C# 1.0
using System;
using System.IO;

class App
{
    static void Main()
    {
        try
        {
            File.ReadAllText("missing.txt");
        }
        catch (IOException e)
        {
            Console.WriteLine("io: " + e.Message);
        }
        catch (FileNotFoundException e)      // can never be reached
        {
            Console.WriteLine("not found: " + e.FileName);
        }
    }
}
