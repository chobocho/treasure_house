// 슬라이드 p10-v9-rec-printmembers — PrintMembers 를 직접, C# 9.0
using System;
using System.Text;

record Login(string User, string Password)
{
    protected virtual bool PrintMembers(StringBuilder builder)
    {
        builder.Append("User = ").Append(User);
        builder.Append(", Password = ***");
        return true;
    }
}

record AdminLogin(string User, string Password, int Level)
    : Login(User, Password);

class App
{
    static void Main()
    {
        Console.WriteLine(new Login("ann", "hunter2"));
        Console.WriteLine(new AdminLogin("bob", "s3cret", 9));
    }
}
