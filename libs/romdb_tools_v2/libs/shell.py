import subprocess


class Command:
    """
    Simple class to store and execute a command line command.
    """
    def __init__(self, pu_cmd):
        self.u_cmd = pu_cmd.strip()
        self.b_executed = False
        self.u_stdout = None
        self.u_stderr = None

    def __str__(self):
        u_output = u'<Command>\n'
        u_output += u'  .u_cmd:      %s\n' % self.u_cmd
        u_output += u'  .b_executed: %s\n' % self.b_executed

        if not self.u_stdout:
            u_output += u'  .u_stdout:   %s\n' % self.u_stdout
        else:
            i_line = 0
            for u_line in self.u_stdout.splitlines():
                i_line += 1
                if i_line == 1:
                    u_output += u'  .u_stdout:   %s\n' % u_line
                else:
                    u_output += u'               %s\n' % u_line

        if not self.u_stderr:
            u_output += u'  .u_stderr:   %s\n' % self.u_stderr
        else:
            i_line = 0
            for u_line in self.u_stderr.splitlines():
                i_line += 1
                if i_line == 1:
                    u_output += u'  .u_stderr:   %s\n' % u_line
                else:
                    u_output += u'               %s\n' % u_line

        return u_output.encode('utf8')

    def execute(self):
        """
        Method to execute the command.
        :return:
        """
        if not self.b_executed:
            self.b_executed = True
            o_process = subprocess.Popen(self.u_cmd.encode('utf8'),
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         shell=True)

            u_stdout, u_stderr = o_process.communicate()

            self.u_stdout = u_stdout.decode('utf8')
            self.u_stderr = u_stderr.decode('utf8')

    def execute_bg(self):
        if not self.b_executed:
            self.b_executed = True
            o_process = subprocess.Popen(self.u_cmd.encode('utf8'),
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         shell=True)
